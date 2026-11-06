# LabAssist User Catalog

This document lists the **bundled application definitions**, not the contents of your database. Form search reads only active tests from the database; applying the patch alone does not add tests to search results.

## How to use this catalog
1. Match the test name and measurement identity to the laboratory report. Percentage and absolute results, total and free measurements, and directly measured and calculated results are distinct.
2. Panels are data-entry shortcuts only. Fill in only the rows actually present in the report and leave all other rows completely blank.
3. Enter units and reference ranges exactly as reported. Suggested units are neither clinical validation nor automatic unit conversion.
4. If the identity is unclear, do not substitute another test. This catalog provides neither clinical interpretation nor recommendations to order tests.

## Coverage
- 65 definitions: 25 hematology, 32 chemistry, 5 endocrinology, and 3 coagulation.
- 14 panels; 62 definitions belong to at least one panel, and 3 are standalone.
- 70 panel memberships, counting tests that belong to more than one panel.
- The three standalone definitions are `CHEM_URIC_ACID`, `INFLAM_CRP`, and `HEM_ESR`. Being standalone is not a defect.
- The original 51 definitions and seven panels retain their names, codes, order, and memberships.

## All definitions

| Code | Name | Category | Existing suggested units | Panels |
|---|---|---|---|---|
| `CBC_WBC` | White blood cell count | hematology | 10^9/L, 10^3/µL | builtin-cbc, builtin-cbc-extended |
| `CBC_RBC` | Red blood cell count | hematology | 10^12/L, 10^6/µL | builtin-cbc, builtin-cbc-extended |
| `CBC_HGB` | Hemoglobin | hematology | g/dL, g/L | builtin-cbc, builtin-cbc-extended |
| `CBC_HCT` | Hematocrit | hematology | %, L/L | builtin-cbc, builtin-cbc-extended |
| `CBC_MCV` | Mean corpuscular volume | hematology | fL | builtin-cbc, builtin-cbc-extended |
| `CBC_MCH` | Mean corpuscular hemoglobin | hematology | pg | builtin-cbc, builtin-cbc-extended |
| `CBC_MCHC` | Mean corpuscular hemoglobin concentration | hematology | g/dL, g/L | builtin-cbc, builtin-cbc-extended |
| `CBC_PLT` | Platelet count | hematology | 10^9/L, 10^3/µL | builtin-cbc, builtin-cbc-extended |
| `CHEM_CREATININE` | Creatinine | chemistry | mg/dL, µmol/L | builtin-renal |
| `CHEM_UREA` | Urea | chemistry | mg/dL, mmol/L | builtin-renal |
| `CHEM_BUN` | Blood urea nitrogen (BUN) | chemistry | mg/dL | builtin-renal |
| `CHEM_SODIUM` | Sodium | chemistry | mmol/L, mEq/L | builtin-electrolytes |
| `CHEM_POTASSIUM` | Potassium | chemistry | mmol/L, mEq/L | builtin-electrolytes |
| `CHEM_CHLORIDE` | Chloride | chemistry | mmol/L, mEq/L | builtin-electrolytes |
| `CHEM_ALT` | Alanine aminotransferase (ALT) | chemistry | U/L | builtin-liver |
| `CHEM_AST` | Aspartate aminotransferase (AST) | chemistry | U/L | builtin-liver |
| `CHEM_ALP` | Alkaline phosphatase (ALP) | chemistry | U/L | builtin-liver |
| `CHEM_GGT` | Gamma-glutamyl transferase (GGT) | chemistry | U/L | builtin-liver |
| `CHEM_BILIRUBIN_TOTAL` | Bilirubin — total | chemistry | mg/dL, µmol/L | builtin-liver |
| `CHEM_BILIRUBIN_DIRECT` | Bilirubin — direct | chemistry | mg/dL, µmol/L | builtin-liver |
| `CHEM_ALBUMIN` | Albumin | chemistry | g/dL, g/L | builtin-liver |
| `CHEM_PROTEIN_TOTAL` | Protein — total | chemistry | g/dL, g/L | builtin-liver |
| `LIPID_CHOLESTEROL_TOTAL` | Cholesterol — total | chemistry | mg/dL, mmol/L | builtin-lipids |
| `LIPID_HDL` | HDL cholesterol | chemistry | mg/dL, mmol/L | builtin-lipids |
| `LIPID_LDL_DIRECT` | LDL cholesterol — directly measured | chemistry | mg/dL, mmol/L | builtin-lipids |
| `LIPID_LDL_CALCULATED` | LDL cholesterol — calculated | chemistry | mg/dL, mmol/L | builtin-lipids |
| `LIPID_TRIGLYCERIDES` | Triglycerides | chemistry | mg/dL, mmol/L | builtin-lipids |
| `GLUCOSE_FASTING` | Glucose — fasting | chemistry | mg/dL, mmol/L | builtin-glycemia |
| `GLUCOSE_RANDOM` | Glucose — random | chemistry | mg/dL, mmol/L | builtin-glycemia |
| `HBA1C` | Hemoglobin A1c (HbA1c) | chemistry | %, mmol/mol | builtin-glycemia |
| `THYROID_TSH` | Thyroid-stimulating hormone (TSH) | endocrinology | mIU/L, µIU/mL | builtin-thyroid |
| `THYROID_FT4` | Thyroxine (T4) — free | endocrinology | ng/dL, pmol/L | builtin-thyroid |
| `THYROID_FT3` | Triiodothyronine (T3) — free | endocrinology | pg/mL, pmol/L | builtin-thyroid |
| `THYROID_T4_TOTAL` | Thyroxine (T4) — total | endocrinology | µg/dL, nmol/L | builtin-thyroid |
| `THYROID_T3_TOTAL` | Triiodothyronine (T3) — total | endocrinology | ng/dL, nmol/L | builtin-thyroid |
| `DIFF_NEUT_PCT` | Neutrophils — percent of leukocytes, blood | hematology | % | builtin-differential-percent |
| `DIFF_NEUT_ABS` | Neutrophils — absolute count, blood | hematology | x 10(9)/L | builtin-differential-absolute |
| `DIFF_LYMPH_PCT` | Lymphocytes — percent of leukocytes, blood | hematology | % | builtin-differential-percent |
| `DIFF_LYMPH_ABS` | Lymphocytes — absolute count, blood | hematology | x 10(9)/L | builtin-differential-absolute |
| `DIFF_MONO_PCT` | Monocytes — percent of leukocytes, blood | hematology | % | builtin-differential-percent |
| `DIFF_MONO_ABS` | Monocytes — absolute count, blood | hematology | x 10(9)/L | builtin-differential-absolute |
| `DIFF_EOS_PCT` | Eosinophils — percent of leukocytes, blood | hematology | % | builtin-differential-percent |
| `DIFF_EOS_ABS` | Eosinophils — absolute count, blood | hematology | x 10(9)/L | builtin-differential-absolute |
| `DIFF_BASO_PCT` | Basophils — percent of leukocytes, blood | hematology | % | builtin-differential-percent |
| `DIFF_BASO_ABS` | Basophils — absolute count, blood | hematology | x 10(9)/L | builtin-differential-absolute |
| `CBC_RDW_CV` | Red cell distribution width — CV, blood | hematology | % | builtin-cbc-extended |
| `CBC_RDW_SD` | Red cell distribution width — SD, blood | hematology | fL | builtin-cbc-extended |
| `CBC_MPV` | Mean platelet volume, blood | hematology | fL | builtin-cbc-extended |
| `RETIC_PCT` | Reticulocytes — percent of erythrocytes, blood | hematology | % | builtin-reticulocytes |
| `RETIC_ABS` | Reticulocytes — absolute count, blood | hematology | x 10(9)/L | builtin-reticulocytes |
| `RETIC_IRF_PCT` | Immature reticulocyte fraction — percent of reticulocytes, blood | hematology | % | builtin-reticulocytes |
| `COAG_PT` | Prothrombin time (PT) | coagulation | None; use the report | builtin-coagulation |
| `COAG_INR` | International normalized ratio (INR) | coagulation | None; use the report | builtin-coagulation |
| `COAG_APTT` | Activated partial thromboplastin time (aPTT) | coagulation | None; use the report | builtin-coagulation |
| `CHEM_CALCIUM_TOTAL` | Calcium — total, blood | chemistry | None; use the report | builtin-minerals |
| `CHEM_CALCIUM_IONIZED` | Calcium — ionized, blood | chemistry | None; use the report | builtin-minerals |
| `CHEM_MAGNESIUM` | Magnesium, blood | chemistry | None; use the report | builtin-minerals |
| `CHEM_PHOSPHATE` | Phosphate, blood | chemistry | None; use the report | builtin-minerals |
| `CHEM_URIC_ACID` | Uric acid, blood | chemistry | None; use the report | Standalone |
| `IRON_SERUM` | Iron, serum | chemistry | None; use the report | builtin-iron |
| `IRON_FERRITIN` | Ferritin, blood | chemistry | None; use the report | builtin-iron |
| `IRON_TIBC` | Total iron-binding capacity (TIBC), blood | chemistry | None; use the report | builtin-iron |
| `IRON_TRANSFERRIN` | Transferrin, blood | chemistry | None; use the report | builtin-iron |
| `INFLAM_CRP` | C-reactive protein (CRP) — quantitative, blood | chemistry | None; use the report | Standalone |
| `HEM_ESR` | Erythrocyte sedimentation rate (ESR) | hematology | None; use the report | Standalone |

## Panels

### `builtin-cbc` — Existing, unchanged
CBC — basic indices (no differential)

`CBC_WBC`, `CBC_RBC`, `CBC_HGB`, `CBC_HCT`, `CBC_MCV`, `CBC_MCH`, `CBC_MCHC`, `CBC_PLT`

### `builtin-renal` — Existing, unchanged
Renal markers — creatinine and urea

`CHEM_CREATININE`, `CHEM_UREA`, `CHEM_BUN`

### `builtin-electrolytes` — Existing, unchanged
Electrolytes — basic

`CHEM_SODIUM`, `CHEM_POTASSIUM`, `CHEM_CHLORIDE`

### `builtin-liver` — Existing, unchanged
Liver-related markers

`CHEM_ALT`, `CHEM_AST`, `CHEM_ALP`, `CHEM_GGT`, `CHEM_BILIRUBIN_TOTAL`, `CHEM_BILIRUBIN_DIRECT`, `CHEM_ALBUMIN`, `CHEM_PROTEIN_TOTAL`

### `builtin-lipids` — Existing, unchanged
Lipid markers

`LIPID_CHOLESTEROL_TOTAL`, `LIPID_HDL`, `LIPID_LDL_DIRECT`, `LIPID_LDL_CALCULATED`, `LIPID_TRIGLYCERIDES`

### `builtin-glycemia` — Existing, unchanged
Glucose and HbA1c

`GLUCOSE_FASTING`, `GLUCOSE_RANDOM`, `HBA1C`

### `builtin-thyroid` — Existing, unchanged
Thyroid markers

`THYROID_TSH`, `THYROID_FT4`, `THYROID_FT3`, `THYROID_T4_TOTAL`, `THYROID_T3_TOTAL`

### `builtin-cbc-extended` — New
CBC — extended indices (no differential)

`CBC_WBC`, `CBC_RBC`, `CBC_HGB`, `CBC_HCT`, `CBC_MCV`, `CBC_MCH`, `CBC_MCHC`, `CBC_PLT`, `CBC_RDW_CV`, `CBC_RDW_SD`, `CBC_MPV`

### `builtin-differential-percent` — New
Leukocyte differential — percentages

`DIFF_NEUT_PCT`, `DIFF_LYMPH_PCT`, `DIFF_MONO_PCT`, `DIFF_EOS_PCT`, `DIFF_BASO_PCT`

### `builtin-differential-absolute` — New
Leukocyte differential — absolute counts

`DIFF_NEUT_ABS`, `DIFF_LYMPH_ABS`, `DIFF_MONO_ABS`, `DIFF_EOS_ABS`, `DIFF_BASO_ABS`

### `builtin-reticulocytes` — New
Reticulocytes — reported parameters

`RETIC_PCT`, `RETIC_ABS`, `RETIC_IRF_PCT`

### `builtin-coagulation` — New
Coagulation — PT, INR and aPTT

`COAG_PT`, `COAG_INR`, `COAG_APTT`

### `builtin-minerals` — New
Minerals — reported blood measurements

`CHEM_CALCIUM_TOTAL`, `CHEM_CALCIUM_IONIZED`, `CHEM_MAGNESIUM`, `CHEM_PHOSPHATE`

### `builtin-iron` — New
Iron-related measurements

`IRON_SERUM`, `IRON_FERRITIN`, `IRON_TIBC`, `IRON_TRANSFERRIN`


Sources for the new definitions: [expansion-sources.md](expansion-sources.md). The new panels are local groupings for data entry, not claims of standardized panel composition or clinical recommendations.
