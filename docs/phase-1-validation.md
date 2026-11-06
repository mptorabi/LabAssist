# Phase 1: local foundation and validation

## Scope and baseline

Prepared against upstream commit `42eddba8984704b412fa31993f62c2cf4fba8ed4`
on branch `phase-1-local-foundation`.

Changes:

- English root README and corrected implementation status.
- Private local secret initialization, without automatic key rotation or database access.
- Explicit environment overrides, strict debug parsing and debug off by default.
- Loopback-only allowed hosts; HTTP limitations documented, not hidden.
- Git exclusions for local secrets and common SQLite backup suffixes.
- Windows/PyCharm setup/update guidance and manual stopped-database backup/restore.
- Eleven isolated configuration regression tests.

No models, migrations, catalogue definitions, units, panels or clinical logic changed.
No catalogue installers were run against an installation database. No patient
backup, local secret or database is included in the release package.
`docs/catalog/expansion-sources.md` is outside this change.

## Executed checks

Environment: Linux, Python 3.11.16, Django 5.2.19, asgiref 3.13.0,
sqlparse 0.6.1. These are the tested versions, not a new dependency lock.

| Check | Result |
| --- | --- |
| `python manage.py test core.test_local_config` | 11 tests passed in 0.328 seconds |
| `python manage.py check` | No issues |
| `python manage.py makemigrations --check --dry-run` | No changes detected |
| `git diff --check` | Passed |
| `python manage.py check --deploy` | Four expected local-HTTP warnings: W004, W008, W012, W016 |

Regression tests cover initialization, stable keys on rerun, independent keys for
separate installations, missing/invalid keys, environment precedence, no silent
fallback, preservation of invalid existing key files, and strict debug parsing.
They use temporary directories and do not access a patient database.

The four deployment warnings concern HSTS, HTTPS redirection and Secure cookies.
They remain visible because this is a local HTTP profile, **not a network-ready
production deployment**. See [local setup](local-setup.md).

## Not completed here

- The full Django suite was started but interrupted before completion. No full-suite
  pass is claimed for this change. The prior baseline passed 326 tests; the new
  eleven tests bring expected discovery to 337 if the baseline is unchanged.
- Windows PowerShell/PyCharm execution and a real browser smoke test were not run
  in this Linux environment.
- The manual backup/restore instructions have not been executed end-to-end on
  Windows. Validate them with a synthetic database before relying on them.
- No production database upgrade, catalogue installation or GitHub push was performed.

## User acceptance checklist

Use the project interpreter in PowerShell, after copying the changes and creating
the local key. The full suite may take several minutes:

```powershell
.\.venv\Scripts\python.exe -m config.local_setup
.\.venv\Scripts\python.exe manage.py test
```

Django's runner creates a separate test database. Do not override its database
settings to point to patient records. Do not run catalogue installation commands
manually as part of this validation.

Then verify:

- [ ] The full suite finishes with `OK`.
- [ ] Normal local startup works with debug unset/false.
- [ ] Login and CSS/JavaScript work using the documented loopback launch command.
- [ ] Existing patients/reports/history remain visible; no catalogue reinstall is needed.
- [ ] A second initialization keeps the original key unchanged.
- [ ] `.local/`, databases and backups do not appear in `git status --short`.
- [ ] A stopped synthetic-database backup passes integrity checks and a separate restore drill.

Only mark these items complete after actually testing them. Keep patient names,
keys, raw database contents and identifying screenshots out of shared test logs.
