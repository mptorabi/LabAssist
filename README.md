# LabAssist

LabAssist is a local Django/SQLite application for recording laboratory results
and reviewing patient history on Windows. The interface and documentation are
in English. Normal application use is offline; initial dependency installation
requires Internet access or a prepared offline package source.

**Recorded data is not independently verified. LabAssist does not diagnose,
recommend treatment, or replace the original laboratory report or clinical judgment.**
Panel presets are data-entry shortcuts, not clinical recommendations.

## Current capabilities

- Patient records and permission-controlled views.
- Individual results and grouped laboratory reports with multi-result entry,
  review before saving, panel selection, and per-row dates.
- Searchable bundled catalogue definitions, aliases, units and panel presets.
- Recorded values, units and reference ranges preserved without automatic inference.
- Patient history and conservative numeric charts; non-numeric results remain visible.

PDF export, automated evidence-based interpretation, OCR, complete structured
microbiology results, and a full audited correction workflow are **not implemented**.
Catalogue coverage is partial, not a claim of clinical completeness.

## Start here

See [local setup and security](docs/local-setup.md) for the full Windows/PyCharm
instructions, including existing installations. From the repository root in
PowerShell, for a **new installation only**:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m config.local_setup
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --insecure
```

Open <http://127.0.0.1:8000/>. This is a **loopback-only local launcher**, not a
production web server. `--insecure` serves bundled CSS/JavaScript while `DEBUG`
remains false; it does not enable HTTPS. Never bind this profile to `0.0.0.0` or
publish it to a network. See the setup guide for limitations.

This phase was validated with Python 3.11.16. Django's supported Python
versions still apply; `requirements.txt` currently permits Django 5.2.x rather
than locking an exact dependency environment.

A new database is empty. Installing bundled catalogue data is a separate,
explicit database operation, **not part of these startup or update steps**.
Read the [catalogue guide](docs/catalog/USER-CATALOG.md), review command help,
and use a disposable database before considering an installation on real data.

## Development checks

Initialize a private local key first. Then run:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
```

Django tests use a separate test database. Use synthetic fixtures only. Do not
supply patient databases to test tools. See the [phase 1 report](docs/phase-1-validation.md)
for the tested environment and results rather than treating a test count as a
permanent product requirement.

## Documentation

- [Local setup, secrets and safe updates](docs/local-setup.md)
- [Backup and restore](docs/backup-restore.md)
- [Product requirements and implementation status](docs/product_requirements.md)
- [Catalogue user guide](docs/catalog/USER-CATALOG.md)
- [Phase 1 change and validation report](docs/phase-1-validation.md)

## Sensitive data

Never commit patient records, screenshots containing identifiers, databases,
exports, backups or secrets. `.gitignore` is only a guardrail: it does not encrypt
files or remove files already tracked by Git. Git/GitHub is a source-code backup,
**not** a patient-data backup. Protect the computer, local account, disks and
backup storage; SQLite files are not encrypted by this application.
