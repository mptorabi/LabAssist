# Blood differential — initial catalog extension

## Scope

Ten local numeric result identities:
five leukocyte percentages and five absolute counts in blood.

These definitions are entry identities, not ordering recommendations.
They are not LOINC mappings.

## Sources

S1 — MedlinePlus Medical Encyclopedia: Blood differential test
https://medlineplus.gov/ency/article/003657.htm

Evidence used:
- Lists neutrophils, lymphocytes, monocytes, eosinophils and basophils.
- Describes percentages of all white blood cells.
- Supports percentage result identities and the "%" spelling.

S2 — Mayo Clinic Laboratories:
Complete Blood Cell Count (CBC) with Differential, Blood; test ID CBC
https://www.mayocliniclabs.com/test-catalog/overview/9109/complete-blood-cell-count-cbc-with-differential-blood

Evidence used:
- Lists absolute counts for all five cell types.
- Uses "x 10(9)/L" for these absolute counts.

## Per-code evidence

| Local code | Result identity | Suggested unit | Source |
|---|---|---|---|
| DIFF_NEUT_PCT | Neutrophils / leukocytes, blood | % | S1 |
| DIFF_NEUT_ABS | Neutrophils, absolute count, blood | x 10(9)/L | S2 |
| DIFF_LYMPH_PCT | Lymphocytes / leukocytes, blood | % | S1 |
| DIFF_LYMPH_ABS | Lymphocytes, absolute count, blood | x 10(9)/L | S2 |
| DIFF_MONO_PCT | Monocytes / leukocytes, blood | % | S1 |
| DIFF_MONO_ABS | Monocytes, absolute count, blood | x 10(9)/L | S2 |
| DIFF_EOS_PCT | Eosinophils / leukocytes, blood | % | S1 |
| DIFF_EOS_ABS | Eosinophils, absolute count, blood | x 10(9)/L | S2 |
| DIFF_BASO_PCT | Basophils / leukocytes, blood | % | S1 |
| DIFF_BASO_ABS | Basophils, absolute count, blood | x 10(9)/L | S2 |

## Identity boundaries

- Percentages and absolute counts are separate tests.
- Percentages refer to all leukocytes, not lymphocyte subsets.
- These definitions are for blood, not other body fluids.
- Method is unspecified; automated/manual equivalence is not asserted.
- Do not automatically map explicitly method-qualified results here.
- Do not merge bands, segmented neutrophils, or immature granulocytes
  into the generic neutrophil identities.
- Do not calculate absolute counts from WBC and percentages.
- Do not infer an identity from an ambiguous label such as "NEUT".
- No aliases or external terminology mappings are added in this batch.

## Deliberately not imported

The sources' reference intervals, clinical interpretation, specimen
handling requirements and laboratory-specific methods are not defaults
for LabAssist.

Mayo's EDTA specimen and instrument details describe its own service;
they must not be assigned to every imported blood differential report.

## Implementation boundary

Sources are recorded in this repository document.
This batch does not populate CatalogTest.source_urls or database
metadata fields. Blood context is explicit in the display names;
structured specimen and method fields remain unchanged.

The existing basic CBC panel is unchanged.
These ten tests are initially standalone catalog entries.
Unit suggestions never select or convert a reported result's unit.
