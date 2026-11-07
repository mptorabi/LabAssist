# LabAssist Product Requirements

## Product goal

Help non-specialist users enter laboratory results easily,
review understandable evidence-based information, and generate
an offline PDF report that helps a clinician review results
and longitudinal history.

The application does not replace clinical judgment.
User-entered data is not independently verified.

## Operating constraints

- Run locally on Windows.
- Work fully offline at runtime.
- Use an English-language interface.
- Use Django and SQLite.
- Use synthetic data during development and testing.
- Keep patient data, secrets and local databases out of Git.

## Main user workflow

1. Create or select a patient profile.
2. Start a laboratory report entry.
3. Enter shared report information once.
4. Select tests individually or through editable panel presets.
5. Enter multiple results in one form.
6. Review and correct entries before saving.
7. View recorded results and longitudinal history.
8. View supported explanations and their limitations.
9. Generate a PDF for clinician review.

## Laboratory test catalogue

Provide an offline, versioned catalogue with searchable names,
abbreviations and aliases.

Planned coverage includes:

- Hematology and differential counts.
- Biochemistry, glucose and lipid testing.
- Kidney and liver testing.
- Electrolytes and minerals.
- Thyroid testing.
- Reproductive hormones and women's and men's reproductive health.
- Pregnancy-related testing.
- Urinalysis, microscopy and timed urine collections.
- Iron studies, vitamins and nutritional markers.
- Coagulation.
- Inflammation, immunology and serology.
- Microbiology and cultures.
- Stool testing and other laboratory categories.

This is a coverage plan, not a claim of complete support.
Catalogue entries must be reviewed before release.

Panel presets are editable selections, not universal definitions.
Users must be able to record tests that are not in the catalogue.

## Data-entry requirements

- Preserve the reported value exactly as entered.
- Support numbers, text, qualitative results and comparison signs.
- Provide structured result formats where a single value is insufficient.
- Preserve reported units and reference ranges.
- Never silently infer a missing unit or reference range.
- Allow reference ranges to include text, not only numeric limits.
- Support relevant specimen information.
- Support relevant context such as fasting status, collection time,
  pregnancy information, menstrual-cycle day and timed collection duration.
- Do not require sensitive context when it is irrelevant.
- Do not assume that all results on one report share a collection date.
- Preserve existing standalone results when introducing report grouping.
- Avoid silently changing historical results when catalogue entries change.

## Explanations and clinical boundaries

Recording support and interpretation support are separate capabilities.

A result may be recorded, displayed and exported even when no
automated interpretation is available.

Any automated finding must:

- Identify the input data used.
- Identify the rule and its version.
- Provide its evidence source.
- State missing information and limitations.
- Be reviewed and tested before clinical use.

Do not infer a diagnosis from a single result.
Do not equate an in-range result with proof of health.
Do not provide unsupported treatment recommendations.

## Longitudinal review

- Show test dates, values, units and reported reference ranges.
- Keep different patients' results separate.
- Distinguish collection or test dates from data-entry timestamps.
- Do not plot or compare incompatible results as if equivalent.
- Preserve non-numeric results in the history.

## PDF output

Generate PDF files fully offline.

Include:

- Necessary patient identifiers.
- Report generation date.
- Recorded laboratory results and their dates.
- Relevant longitudinal history.
- Clear separation of entered data and automated explanations.
- Sources and rule versions for any automated findings.
- Missing-data notices and limitations.
- A notice that entered data is not independently verified.

The PDF does not replace the original laboratory report.
Users should be warned that exported files contain sensitive data.

## Future import support

Photo or PDF extraction may be added later only if it can run offline.

Extracted values, units, dates and patient associations must be
reviewed and confirmed by the user before saving.

## Current implementation

Status is based on the repository reviewed at `42eddba` plus the phase 1 local
foundation changes. This section describes implemented capabilities, not clinical
validation or a claim of complete catalogue coverage.

- Patient records, individual result entry and permission-controlled views.
- Grouped laboratory reports and multi-result entry with review before saving.
- Editable panel selections and searchable active tests/aliases.
- Bundled catalogue definitions, units and additive panel installation commands.
  Catalogue installation remains separate from application startup and code updates.
- Shared report metadata and per-result date overrides.
- Per-patient result lists, per-test history and conservative numeric charts.
- Recorded notes and a single-result recorded-data report page.
- Private local secret initialization, debug disabled by default and loopback hosts.
- English setup/update instructions and a manual backup/restore procedure.

The pre-phase-1 baseline passed 326 Django tests. Current phase validation is
recorded in [phase-1-validation.md](phase-1-validation.md); test counts are not a
fixed requirement or a substitute for clinical/security review.

Not yet implemented or incomplete:

- Complete reviewed catalogue coverage; user-facing entry of uncatalogued tests.
- Full correction/voiding workflows and an audit trail identifying who changed what.
- Historical catalogue snapshots/versioning for recorded results.
- Structured specimen/context capture and complex result formats.
- Evidence-based interpretation, PDF export and photo/PDF extraction.
- Automated backup scheduling and a built-in restore workflow.
- Patient-level access partitioning and a network deployment profile.

## Next implementation milestones

1. Validate the phase 1 local setup and backup/restore drill on Windows.
2. Add attributable, auditable corrections to patient and report records.
3. Generate an offline PDF containing recorded results and relevant history.
4. Improve patient search, pagination and browser-level regression coverage.
5. Expand reviewed catalogue coverage, specimen/context and result structures.
6. Add narrowly scoped, evidence-based explanations only with reviewed rules,
   sources, versions, limitations and tests.
