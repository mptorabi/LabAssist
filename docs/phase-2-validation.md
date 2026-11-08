# Phase 2: attributed creation and safe corrections

## Scope

Patient, LabReport and LabResult creation through the supported application web
forms now records the authenticated creator and a creation audit event.
Correction pages require the existing view permissions and the corresponding
`change_patient`, `change_labreport` or `change_labresult` permission for POST.
View-only users can inspect history but cannot submit corrections. Permissions
are model-level, not patient-level; this release adds no tenancy or patient ACLs.

Patient corrections allow name, date of birth and recorded sex assigned at birth.
Report corrections allow laboratory name, report number, issue date and notes.
Result corrections allow test date, reported value, unit, reference range and notes.
Patient/report/test database identities cannot be reassigned. Header corrections
do not cascade to result dates or values. No conversions, clinical interpretation,
catalog installation, test merging or inferred units are introduced.

Each correction requires a reason (1–1000 characters after trimming). The service
uses a conditional revision update inside a transaction. A stale form receives
HTTP 409; reload and compare before resubmitting. Validation, no-op changes and
audit failures roll back the record and revision. SQLite lock errors are reported
as retryable failures; reload before retrying. This is not a general idempotency
mechanism for creation forms. Tests cover stale submissions, not a multi-process
load/concurrency benchmark.

## History and limitations

History stores actor ID, username at event time, timestamp, reason, revision and
before/after snapshots. History is paginated (25 events). Legacy creators remain
NULL and revisions start at zero; no retrospective events or attribution are
fabricated. The first correction of a legacy record captures its previous values.
Creator/actor accounts are protected against deletion; deactivate them instead.

This is an application-managed audit trail, NOT a tamper-proof ledger. Raw SQL,
ORM saves/updates, shell scripts, imports and future code can bypass it. Supported
writes must use `core.audit.create_record` / `correct_record`. Audit history has
no edit/delete web interface. Patient and result admin screens are view-only,
even for superusers. LabReport remains unregistered in admin. Catalog admin
behavior is unchanged. Two former patient-admin creation tests now assert denial
because un-attributed admin creation is intentionally unsupported.

Snapshots contain sensitive patient data, including old values. Protect backups
and audit data just like current clinical records. Retention/redaction policies,
external audit anchoring, deletion workflows and patient reassignment are outside
this phase. A result correction does not increment its parent report revision;
revisions are per record, not per report aggregate.

## Schema changes

- core/0001_initial: RecordAudit table and unique record/type/revision constraint.
- patients/0003: nullable protected created_by FK and revision default 0.
- labs/0009: the same fields for LabReport and LabResult.

No data migration, catalog operation, deletion or clinical backfill is included.
Schema changes still require an approved migration window. Do not start the new
application against an old schema. Do not reverse these migrations after use:
that would discard audit history and attribution. A rollback must restore a
matched backup of code and database; later writes require separate reconciliation.

## Validation

Linux; Python 3.11.16; Django 5.2.19; SQLite; synthetic data only.
Final full suite: **373 tests passed** (337 existing, 36 new).
`manage.py check`: no issues. `makemigrations --check --dry-run`: no changes.
`git diff --check`: clean.

The migration regression test uses Django's disposable test database to rehearse
an upgrade from patients/0002 and labs/0008, preserving every pre-existing field
(including timestamps, links and exact result strings), for linked and standalone
results. It checks NULL legacy creators, zero revisions, no fabricated events,
SQLite integrity and foreign keys. Fresh-schema migrations also ran as part of
test database setup. No operational database migration command or bundled catalog
installation was run. No real patient data or private key was used or packaged.

Not validated here: Windows/PyCharm runtime, browser/manual UI, a real-data backup
restore, production migration duration, concurrent process load, or security
against an administrator with direct database access. Perform those checks locally
as appropriate before adopting this release.
