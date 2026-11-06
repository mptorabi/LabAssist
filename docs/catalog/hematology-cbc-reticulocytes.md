# CBC indices and reticulocytes — catalog extension

## Scope and evidence

Five local entry identities, not ordering recommendations or LOINC mappings.
Sources were read during preparation; only identities and unit spellings below
are used. Reference intervals and clinical interpretations are NOT imported.

| Code | Identity (blood) | Suggested unit | Evidence |
|---|---|---|---|
| CBC_RDW_CV | Red cell distribution width, coefficient of variation | % | S1 |
| CBC_RDW_SD | Red cell distribution width, standard deviation | fL | S1 |
| CBC_MPV | Mean platelet volume | fL | S2 |
| RETIC_PCT | Reticulocytes as percent of all erythrocytes | % | S3, S4 |
| RETIC_ABS | Absolute reticulocyte count | x 10(9)/L | S3 |

S1 — Medscape: Red Cell Distribution Width (RDW) Test
https://emedicine.medscape.com/article/2098635-overview
Explicitly distinguishes RDW-SD (fL) and RDW-CV (%).

S2 — Cleveland Clinic Journal of Medicine: Three neglected numbers in the CBC:
The RDW, MPV, and NRBC count (2019;86:167–172).
https://www.ccjm.org/content/86/3/167
Describes mean platelet volume and reports MPV in fL.

S3 — Mayo Clinic Laboratories: Reticulocyte Profile, Blood (RETB).
https://www.mayocliniclabs.com/test-catalog/overview/616856/reticulocyte-profile-blood
Separately lists reticulocyte percentage and absolute reticulocytes;
uses % and x 10(9)/L respectively. Its other profile components are not imported.

S4 — MyHealth Alberta / Healthwise: Reticulocyte Count.
https://myhealth.alberta.ca/Health/pages/conditions.aspx?hwid=hw203366
Explicitly defines the percentage denominator as total red blood cells,
not leukocytes or the reticulocyte population alone.

## Identity boundaries

- RDW-CV and RDW-SD are independent identities, not interchangeable units.
- Do not automatically map ambiguous RDW or RETIC labels.
- MPV is not platelet count, plateletcrit, or platelet distribution width.
- Reticulocyte percentage is uncorrected percent of erythrocytes.
- Absolute and percentage reticulocytes remain independent; do not calculate
  either from RBC and the other result.
- Corrected reticulocyte counts, RPI, IRF and reticulocyte hemoglobin indices
  are excluded. No aliases or terminology mappings are added.
- No method equivalence is asserted. Do not automatically map explicitly
  method-qualified results to these method-unspecified identities.
- Blood context is explicit in names. Structured specimen/method/time fields
  remain unspecified. Do not copy a source laboratory's collection tube,
  specimen handling or instrument details as universal defaults.

## Implementation boundary

Sources are recorded here, not in CatalogTest.source_urls or database fields.
All five additions are standalone. Existing panels and 45 definitions remain
unchanged. Unit suggestions do not select, convert or derive result values.
No reference intervals, clinical advice, migrations or database installation
are included in this batch.
