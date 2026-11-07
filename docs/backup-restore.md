# Backup and restore (local SQLite)

## Safety rules

- A Git commit/push does not back up patient records.
- Back up before every update, migration, catalogue installation or bulk edit,
  and on a regular schedule suited to how much data you can afford to lose.
- Keep multiple dated versions and at least one protected copy on a separate
  device. Disconnect removable backup media after use where practical.
- Database copies contain patient information and user password hashes. Protect
  them with account permissions and encrypted storage (for example an encrypted
  drive). This application does not encrypt SQLite or backup files.
- Do not send databases or real patient screenshots to GitHub or support chats.
- A backup is not considered usable until a restore has been tested.

This guide uses a **stopped application** backup. It is not a live-copy procedure.
Do not copy a database while Django, a SQLite browser, PyCharm's database tool,
or another process is writing to it. Do not delete SQLite sidecar files to make
an error disappear.

## 1. Stop and record the environment

Stop the server with Ctrl+C and close all database connections, including GUI
tools and other terminals. Keep the application stopped until the copy finishes.
In PowerShell at the repository root:

```powershell
git rev-parse HEAD
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip freeze
```

Save the output with the backup. Record any uncommitted source changes as well;
a commit identifier alone cannot reproduce those changes. Keep a source archive
for the version being backed up if future offline recovery is required. Preserve
Python/dependency installers separately if the recovery computer may be offline.

## 2. Create a new dated backup directory

Replace `E:\LabAssistBackups` with a private, protected destination. Do not use a
public or automatically shared folder. The commands abort if the timestamped
folder already exists, rather than overwriting an earlier backup.

```powershell
$ErrorActionPreference = "Stop"
$backupRoot = "E:\LabAssistBackups"
$backup = Join-Path $backupRoot (Get-Date -Format "yyyyMMdd-HHmmss")
New-Item -ItemType Directory -Path $backup -ErrorAction Stop | Out-Null

if (-not (Test-Path -LiteralPath ".\db.sqlite3" -PathType Leaf)) {
    throw "Database not found. Check the project folder; do not create an empty replacement."
}

# Copy the database and any SQLite transaction sidecars as one stopped set.
foreach ($name in @("db.sqlite3", "db.sqlite3-wal", "db.sqlite3-shm", "db.sqlite3-journal")) {
    if (Test-Path -LiteralPath $name) {
        Copy-Item -LiteralPath $name -Destination $backup -ErrorAction Stop
    }
}

# Keep the local key private. Environment-managed keys need separate secure storage.
if (Test-Path -LiteralPath ".\.local\secret_key") {
    New-Item -ItemType Directory -Path (Join-Path $backup ".local") | Out-Null
    Copy-Item -LiteralPath ".\.local\secret_key" -Destination (Join-Path $backup ".local")
}

git rev-parse HEAD | Out-File (Join-Path $backup "source-commit.txt")
.\.venv\Scripts\python.exe --version 2>&1 | Out-File (Join-Path $backup "python-version.txt")
.\.venv\Scripts\python.exe -m pip freeze | Out-File (Join-Path $backup "packages.txt")
Get-ChildItem -LiteralPath $backup -Filter "db.sqlite3*" |
    Get-FileHash -Algorithm SHA256 |
    Format-List | Out-File (Join-Path $backup "database-hashes.txt")
Write-Host "Backup copied to $backup — verification is still required."
```

A failed command means the backup is incomplete. Do not delete the source database.
Do not resume the application until the copying step has completed or been aborted.

If your installation uses additional uploads or exports, back those up separately
with the same privacy protections. The current database does not embed every
possible external file. Never include `.venv` as a substitute for package records.

## 3. Verify a disposable copy, not the backup master

Copy the database **and all its sidecars** from the backup into a new, private
scratch directory. SQLite may perform transaction recovery when opening a copy,
which is why verification should not operate on the only backup. For example:

```powershell
$verify = Join-Path $backupRoot ("verify-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Path $verify -ErrorAction Stop | Out-Null
Get-ChildItem -LiteralPath $backup -Filter "db.sqlite3*" -File |
    Copy-Item -Destination $verify -ErrorAction Stop
$env:LABASSIST_VERIFY_DB = Join-Path $verify "db.sqlite3"
@'
import os
from pathlib import Path
import sqlite3

path = Path(os.environ["LABASSIST_VERIFY_DB"]).resolve()
# mode=rw refuses to silently create a missing database; recovery is allowed
# only on this disposable copy.
with sqlite3.connect(path.as_uri() + "?mode=rw", uri=True) as connection:
    rows = connection.execute("PRAGMA integrity_check").fetchall()
    if rows != [("ok",)]:
        raise SystemExit("SQLite integrity check failed; preserve all source files.")
    required = {"django_migrations", "auth_user", "patients_patient", "labs_labresult"}
    tables = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    if not required <= tables:
        raise SystemExit("Expected LabAssist tables are missing.")
print("SQLite integrity and required-table checks passed.")
'@ | .\.venv\Scripts\python.exe -
if ($LASTEXITCODE -ne 0) { throw "Backup verification failed." }
Remove-Item Env:LABASSIST_VERIFY_DB
```

An `ok` integrity result is a structural check, not proof that you backed up the
right patients or the latest data. Complete the restore drill below. Treat scratch
copies as patient data; securely manage their retention just like backups.

## 4. Restore drill in a separate installation

1. Leave the original installation and the backup master unchanged.
2. Prepare a **new private directory** with the matching source version and a
   compatible Python environment. Do not run migrations or catalogue installers
   before testing the restored backup.
3. With no server running in that directory, copy the backed-up `db.sqlite3` and
   all saved SQLite sidecars into its root. The destination must not contain an
   older database or unrelated sidecars. Do not mix files from different backups.
4. Restore `.local/secret_key` securely, or supply the original environment-managed
   key. Alternatively generate a new private key; users must sign in again and
   old signed tokens will no longer work. Never restore the public development key.
5. Using that directory's interpreter and working directory, run `manage.py check`.
6. Start `manage.py runserver 127.0.0.1:8001 --insecure` and open
   <http://127.0.0.1:8001/>. Avoid using the original installation simultaneously
   while checking which database you are viewing.
7. Confirm login, expected patient/report/result counts, several known recent
   records, and history. Do not add real corrections in the drill copy.
8. Record the backup date, source version, check result and restore-test date
   without putting patient identifiers in an unsecured verification log.
9. Stop the drill server. Retain or securely remove the drill copy according to
   your data retention rules.

Only after a successful drill should a restored directory replace a broken
installation. Stop all processes first and preserve the old directory separately
for rollback/investigation. Never overwrite the sole remaining database.

## Recovery boundaries

- Restoring an older backup loses changes made after that backup; reconcile them
  deliberately rather than pretending the restore contains current data.
- Restoring to newer code may require migrations. First prove the backup works
  with its matching version, then follow a separately reviewed upgrade plan.
- A missing key does not make patient rows unreadable, but rotating it invalidates
  signed sessions/tokens. A database backup is not encrypted by `SECRET_KEY`.
- This phase provides a manual procedure, not automatic scheduling, encryption,
  a restore button, or a guarantee against disk failure.
