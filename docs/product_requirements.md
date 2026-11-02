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

- Patient records.
- Individual laboratory result entry.
- Per-patient result lists and per-test history.
- Recorded notes and permission checks.
- A single-result recorded-data report page.
- 89 passing automated tests at this milestone.

Not yet implemented:

- A comprehensive preloaded test catalogue.
- Laboratory report grouping and multi-result entry.
- Evidence-based interpretation.
- PDF export.
- Photo or PDF extraction.

## Next implementation milestones

1. Design report grouping and catalogue metadata.
2. Add a reviewed initial catalogue and editable panel presets.
3. Build multi-result entry with review before saving.
4. Generate an initial PDF with recorded results and history.
5. Add narrowly scoped, evidence-based explanations.
6. Expand catalogue coverage and supported result structures.
