# Local setup and security

## Scope

This profile is for one trusted Windows computer, using SQLite and a browser on
that same computer. It is not a LAN/Internet deployment configuration. It does
not isolate patient records between different staff accounts or encrypt the disk.
Use an access-controlled Windows account, screen lock and protected storage.
Avoid shared/cloud-synchronised project folders for real patient data.

## New installation (PowerShell)

Install a supported Python version (this phase was tested with Python 3.11.16), obtain
the source, and open a terminal in the folder containing `manage.py`:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m config.local_setup
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --insecure
```

Using the explicit interpreter avoids PowerShell activation-policy problems.
Initial installation may need Internet; runtime assets are bundled locally.
Open <http://127.0.0.1:8000/> and sign in. The superuser is for initial setup and
administration; create appropriately restricted staff accounts for routine work.
Permissions currently apply by model, not by individual patient assignment.

The database remains at `db.sqlite3` in the repository root. No catalogue install
command is run automatically. An empty catalogue on a new database is expected.

## Private secret and configuration

`python -m config.local_setup` creates `.local/secret_key` using Python's
cryptographic random generator. It does not start Django, open SQLite, run
migrations or install catalogue data. Re-running it leaves an existing file
unchanged, including an invalid file (so investigate an error rather than silently
replacing a key). `.local/` is excluded from Git.

The file persists across restarts. Do not delete it as routine cleanup. On Windows,
protect the directory using your account's filesystem permissions; POSIX mode
flags alone do not enforce Windows ACLs. The key is not printed by the command.

Configuration precedence:

| Setting | Source | Default |
| --- | --- | --- |
| `SECRET_KEY` | `LABASSIST_SECRET_KEY`, otherwise `.local/secret_key` | No shared fallback; startup fails if missing/invalid |
| `DEBUG` | `LABASSIST_DEBUG`: `true`, `false`, `1`, or `0` | `false` |
| `ALLOWED_HOSTS` | Local profile in `config/settings.py` | `localhost`, `127.0.0.1`, `[::1]` |

Environment keys must be private random strings of at least 50 characters;
short/repeated-character keys and the `django-insecure-` prefix are rejected.
These checks are not proof of randomness: use the initializer or a trusted secret
generator. An invalid environment override fails instead of falling back to a file.
`.env` files are **not loaded**; set real process environment variables if needed.
Do not put real secrets into shared PyCharm run configurations.

For development with synthetic data only, in the current PowerShell session:

```powershell
$env:LABASSIST_DEBUG = "true"
# Run development commands here.
Remove-Item Env:LABASSIST_DEBUG
```

Keep debug off when using real patient data. Debug pages can reveal sensitive
configuration and request information.

## PyCharm

1. Select `.venv\Scripts\python.exe` as the project interpreter.
2. Set the working directory to the folder containing `manage.py`.
3. Run the initializer once from the terminal using that interpreter.
4. Configure `manage.py` with parameters
   `runserver 127.0.0.1:8000 --insecure`.
5. Leave `LABASSIST_DEBUG` unset for normal local use. Check existing run
   configurations for older environment overrides.

## Why `--insecure` and remaining deployment warnings?

Django's development server normally serves bundled static assets automatically
only with debug enabled. `--insecure` allows that static-file handling with debug
disabled. It is not a general production server and is not appropriate for public
or LAN exposure. If CSS is missing, verify the exact command before enabling debug.

This profile intentionally uses HTTP on loopback. HTTPS redirection, HSTS and
Secure session/CSRF cookies are not enabled: enabling them without an HTTPS server
would break local access or login. `check --deploy` will therefore still warn
about those HTTPS controls. Warnings are not suppressed and should not be mistaken
for evidence that this profile is ready for network deployment.

`ALLOWED_HOSTS` checks host headers; it is **not a firewall**. Always bind to
`127.0.0.1`. Any future network deployment needs a separate reviewed server,
HTTPS, static-file service, cookie/proxy configuration and access-control design.

## Updating an existing installation

1. Stop the server and all processes using the database.
2. Make and verify a backup using [backup and restore](backup-restore.md).
3. Record the current Git commit and Python/package versions.
4. Review and apply the code update. Preserve your existing `db.sqlite3`.
5. Run `python -m config.local_setup` with the project interpreter.
6. Run `manage.py check` and `manage.py makemigrations --check --dry-run`.
7. Start the loopback server and verify sign-in, styles and existing records.

This phase changes no models and adds no migrations. **Do not run catalogue
installers as part of this update.** Future migrations require their own reviewed
upgrade plan and a verified backup first.

The old source-controlled development key is public. Do not reuse it or retain it
in `SECRET_KEY_FALLBACKS`. Switching to a new key invalidates existing signed
sessions and outstanding signed tokens; sign in again. It does not change patient
records or password hashes. No Git-history rewrite or force-push is required.
