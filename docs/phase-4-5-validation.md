# Phase 4–5 validation

Baseline: a5c696eb2494cbf4b9ce35b06833c78257b0f035 (phase 3).

## Delivered scope
- Patient name/ID search; patient-scoped report laboratory/number search;
  patient/report result test-name/code search. Pagination uses 20 records and
  preserves query parameters. Queries are bounded to 200 characters.
- Optional verbatim specimen, collection time and receipt time text. No date,
  calendar or timezone normalization is attempted.
- Optional explicit Numeric / Qualitative / Text classification. Values remain
  text; classification is never inferred and triggers no calculation.
- New fields participate in entry, review/edit, correction audit and PDF output.
- Offline structural catalog proposal review gate; no catalog additions.

## Verification
- 404 Django tests passed on isolated in-memory SQLite (389 existing + 15 new).
- New coverage includes search boundaries, pagination, patient scope, permissions,
  raw-text retention, invalid input, classification defaults, audit/correction
  revision conflict, and metadata/PDF output independent of screen filtering.
- Catalog checker tests run without permitted database access, including malformed
  JSON, duplicate keys/codes, file size, evidence and review requirements.
- `makemigrations --check --dry-run`: no changes detected.
- `git diff --check`: passed.
- Chromium smoke: login, search with pagination, report paging, metadata and
  classification entry/review/edit/save; no JavaScript page errors. Desktop and
  390px mobile screenshots inspected. Result tables scroll horizontally on mobile.
- Browser data existed only in a separate synthetic SQLite file, not a user DB.

## Boundaries
- Linux verification, not a new Windows test run; local Windows checks remain
  part of deployment acceptance.
- No clinical interpretation, new reference ranges, unit conversion, catalog
  installation, GitHub updates or operational database migration was performed.
- PDF retains its 100-linked-result safety limit and existing earlier-result limit.
- Catalog evidence is structurally checked, not automatically authenticated or
  clinically verified. Expansion requires a separate source-backed review.
- Migration 0010 is additive. Existing records start with blank new fields.
  Do not roll back the schema after entering new metadata; restore matched code
  and database backups if a full rollback is required.
