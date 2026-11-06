# Immature reticulocyte fraction (IRF) — separate follow-up batch

## Scope

One local numeric entry identity, RETIC_IRF_PCT:
Immature reticulocyte fraction — percent of reticulocytes, blood.
Suggested unit: %.
This is an entry identity, not a recommendation to order a test or a LOINC mapping.

## Evidence

Mayo Clinic Laboratories — Reticulocyte Profile, Blood (RETB)
https://www.mayocliniclabs.com/test-catalog/overview/616856/reticulocyte-profile-blood

The source's reference-value section separately lists IMMATURE RETICULOCYTE
FRACTION (IRF) with percentage units. No reference interval is imported.
Its method description defines IRF as the ratio of reticulocytes in the
immature/strong-fluorescence region to the TOTAL RETICULOCYTE count.
That description is specific to the laboratory's Sysmex XN service, not a
universal specification for all instruments.

## Identity boundaries

- The denominator is total reticulocytes, not total erythrocytes or leukocytes.
- RETIC_PCT is percent of erythrocytes; RETIC_IRF_PCT is a different identity.
- IRF is not an absolute immature reticulocyte count, corrected reticulocyte
  percentage, reticulocyte production index (RPI), or an immature platelet fraction.
- Do not infer IRF from a vague label such as 'immature cells'.
- No aliases, method equivalence, automatic calculation or unit conversion.
- Method-qualified results require review; this entry does not assert
  comparability across instruments or fluorescence thresholds.
- Reticulocyte hemoglobin equivalent/content is NOT added here. The source
  describes RET-He as a Sysmex-specific parameter using a proprietary equation;
  CHr and RET-He must not be collapsed into one generic identity without review.
- No tube type, specimen handling, interpretation or reference interval is added.

## Implementation

Standalone entry; no panel or model changes and no database installation.
Structured specimen, method, time_aspect and source_urls remain empty.
Blood context is in the display name; this document records the evidence.
Unit suggestions do not select a reported result's unit.

The preceding CBC/reticulocyte batch excluded IRF deliberately. This document
records a new, separately reviewed extension; it does not retroactively change
that batch's scope.
