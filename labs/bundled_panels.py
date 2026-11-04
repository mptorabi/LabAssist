PANELS = (
    ("builtin-cbc", "CBC — basic indices (no differential)", "hematology", "Hematology", (
        ("CBC_WBC", "White blood cell count"),
        ("CBC_RBC", "Red blood cell count"),
        ("CBC_HGB", "Hemoglobin"),
        ("CBC_HCT", "Hematocrit"),
        ("CBC_MCV", "Mean corpuscular volume"),
        ("CBC_MCH", "Mean corpuscular hemoglobin"),
        ("CBC_MCHC", "Mean corpuscular hemoglobin concentration"),
        ("CBC_PLT", "Platelet count"),
    )),
    ("builtin-renal", "Renal markers — creatinine and urea", "chemistry", "Chemistry", (
        ("CHEM_CREATININE", "Creatinine"),
        ("CHEM_UREA", "Urea"),
        ("CHEM_BUN", "Blood urea nitrogen (BUN)"),
    )),
    ("builtin-electrolytes", "Electrolytes — basic", "chemistry", "Chemistry", (
        ("CHEM_SODIUM", "Sodium"),
        ("CHEM_POTASSIUM", "Potassium"),
        ("CHEM_CHLORIDE", "Chloride"),
    )),
    ("builtin-liver", "Liver-related markers", "chemistry", "Chemistry", (
        ("CHEM_ALT", "Alanine aminotransferase (ALT)"),
        ("CHEM_AST", "Aspartate aminotransferase (AST)"),
        ("CHEM_ALP", "Alkaline phosphatase (ALP)"),
        ("CHEM_GGT", "Gamma-glutamyl transferase (GGT)"),
        ("CHEM_BILIRUBIN_TOTAL", "Bilirubin — total"),
        ("CHEM_BILIRUBIN_DIRECT", "Bilirubin — direct"),
        ("CHEM_ALBUMIN", "Albumin"),
        ("CHEM_PROTEIN_TOTAL", "Protein — total"),
    )),
    ("builtin-lipids", "Lipid markers", "chemistry", "Chemistry", (
        ("LIPID_CHOLESTEROL_TOTAL", "Cholesterol — total"),
        ("LIPID_HDL", "HDL cholesterol"),
        ("LIPID_LDL_DIRECT", "LDL cholesterol — directly measured"),
        ("LIPID_LDL_CALCULATED", "LDL cholesterol — calculated"),
        ("LIPID_TRIGLYCERIDES", "Triglycerides"),
    )),
    ("builtin-glycemia", "Glucose and HbA1c", "chemistry", "Chemistry", (
        ("GLUCOSE_FASTING", "Glucose — fasting"),
        ("GLUCOSE_RANDOM", "Glucose — random"),
        ("HBA1C", "Hemoglobin A1c (HbA1c)"),
    )),
    ("builtin-thyroid", "Thyroid markers", "endocrinology", "Endocrinology", (
        ("THYROID_TSH", "Thyroid-stimulating hormone (TSH)"),
        ("THYROID_FT4", "Thyroxine (T4) — free"),
        ("THYROID_FT3", "Triiodothyronine (T3) — free"),
        ("THYROID_T4_TOTAL", "Thyroxine (T4) — total"),
        ("THYROID_T3_TOTAL", "Triiodothyronine (T3) — total"),
    )),
)

DESCRIPTION = (
    "Entry preset only, not a recommendation to order tests or a complete laboratory panel. "
    "Enter only tests explicitly present on your report. Leave other rows entirely blank. "
    "Copy units and reference ranges from the report; do not infer them. "
    "Use an exact measurement match (for example urea vs BUN, free vs total, "
    "or direct vs calculated). If uncertain, do not substitute another test."
)