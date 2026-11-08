# Phase 3: offline recorded-data PDF

## Scope

Baseline: `da5828451b348ec2dee3bb3f7dac44977f2c38b1` (merged phase 2).
The report detail page offers **Download recorded-data PDF**. The GET endpoint is
`/labs/patients/<patient_pk>/reports/<report_pk>/pdf/` when labs is mounted at `/labs/`.
Use Django's `labs:report_pdf` URL name rather than hard-coding the mount prefix.

The export contains the patient's current recorded identity, report metadata,
current record revisions, all consistently linked results, and related earlier
results. It adds no clinical interpretation, flags, calculations, conversions,
reference ranges, inferred ages, or recommendations. Missing fields explicitly
say `Not recorded`. Test names/codes are current catalog labels, not historical
catalog snapshots. The export is not an original laboratory certificate, signed
report, immutable record, or full correction/audit log.

## Earlier-results rule

Match the same patient and exact LabTest primary key. For each test, include only
dates strictly earlier than that test's earliest date in the selected report.
Exclude the selected report and same-day results. Include ungrouped results when
they satisfy this rule. Different units are preserved; no comparability is
asserted. Sort by descending test date, creation time, then primary key.
Show at most 100 earlier results across all tests, explicitly displaying both
the shown count and total count. This is not a complete patient-history export.

## Privacy and data integrity

- Requires login and all three permissions: `patients.view_patient`,
  `labs.view_labreport`, `labs.view_labresult`. These are existing model-level
  permissions, not newly introduced per-patient access restrictions.
- Report lookup is scoped to the patient URL. A missing/mismatched report is 404.
- Inconsistent patient links in the current report cause HTTP 409, not silent
  omission of records. No PDF or other patient's data is returned.
- Unsupported font characters cause HTTP 422 with a generic explanation; stored
  text must not be altered merely to bypass the font limitation.
- User text is plain text, not HTML; no URLs, images or external resources are
  fetched. CR/LF line endings and tabs are normalized for visual layout only.
- The configured SQLite database is read within one transaction; data is
  materialized before rendering. Other database isolation levels are not validated.
- The export makes no record writes and creates no audit event. Export-access
  auditing is outside this release's scope.
- PDF bytes are generated in memory; no server-side export files are persisted.
  Responses use private/no-store cache directives. Filename and PDF metadata do
  not contain the patient name. Downloaded files still contain sensitive data:
  browser settings, downloads folders, backups, printers and sharing need local
  safeguards. PDFs are not password-encrypted.

## Dependencies and offline operation

Runtime: `fpdf2==2.8.7`, `uharfbuzz==0.55.0` plus their dependencies.
DejaVu Sans is bundled under `labs/pdf_fonts/` with its redistribution license.
HarfBuzz shaping supports the tested Persian/English examples; this is not a
claim of universal Unicode coverage or PDF accessibility certification.
`pypdf==7.0.0` is a test-only dependency in `requirements-test.txt`.

Install using the project interpreter:

```powershell
python -m pip install -r requirements-test.txt
python -m pip check
```

Do not install the legacy `fpdf` package alongside `fpdf2`; both use the `fpdf`
import namespace. Use a clean virtual environment if both are present.

Installation normally needs network access; generation does not. For an offline
Windows machine, prepare wheels on an online machine with the same Python
version and Windows architecture:

```powershell
python -m pip download --only-binary=:all: -r requirements-test.txt -d wheelhouse
# Transfer the requirements files and wheelhouse to the offline machine.
python -m pip install --no-index --find-links=wheelhouse -r requirements-test.txt
```

The release ZIP does not include wheels. It includes the font, so PDF generation
never downloads a font or depends on an operating-system font installation.

## Validation and limits

Linux / Python 3.11 / Django 5.2.19: system check, migration drift check, all
389 tests (16 PDF-specific tests), and whitespace diff check passed for this
release. Tests use an isolated in-memory SQLite database and synthetic data.
The socket-blocking export test passed. No production migration or catalog
installer was executed. Windows CPython 3.14 x64 binary wheel resolution was
checked, but this is not a Windows runtime test.

Visual review: a synthetic Persian/English single-page report, scientific unit
symbols and comparison value, and page 2 of a long mixed-language report.
Word wrapping, identifiers on continuation pages, and footer placement were
checked. Long unbroken values/notes are also covered by an automated test.
Windows/PyCharm browser download and real PDF-viewer acceptance remain required.
Very large imported reports/notes have no export-specific resource quota; only
the earlier-results section is capped. This remains a local loopback deployment,
not an Internet-facing export service. The current report is exported, not a
standalone ungrouped result. No new migrations are introduced.

## Windows acceptance checklist

Run in the project's activated virtual environment after installing dependencies:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Use an existing properly initialized test installation with phase-2 schema. Do
not initialize, upgrade or seed the operational database for this check.

- Download a synthetic report while disconnected from the Internet.
- Check Persian names, `<0.01`, scientific units, blank fields and long notes.
- Confirm page identifiers/footers and earlier-results scope/counts.
- Test a reader with all three view permissions, a user missing one permission,
  anonymous access, and a patient/report URL mismatch.
- Verify no diagnosis or high/low flag is newly generated.
- Treat the downloaded PDF as confidential; delete synthetic test exports after review.

Do not run `migrate` or `install_bundled_*` as part of applying this package.
Any pending phase-2 operational migration remains a separate approved task.
