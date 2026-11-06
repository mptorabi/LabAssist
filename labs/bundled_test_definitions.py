# Fields:
# code, name, category_code, category_name, input_type

TEST_DEFINITIONS = (
    (
        "CBC_WBC", "White blood cell count",
        "hematology", "Hematology", "numeric",
    ),
    (
        "CBC_RBC", "Red blood cell count",
        "hematology", "Hematology", "numeric",
    ),
    (
        "CBC_HGB", "Hemoglobin",
        "hematology", "Hematology", "numeric",
    ),
    (
        "CBC_HCT", "Hematocrit",
        "hematology", "Hematology", "numeric",
    ),
    (
        "CBC_MCV", "Mean corpuscular volume",
        "hematology", "Hematology", "numeric",
    ),
    (
        "CBC_MCH", "Mean corpuscular hemoglobin",
        "hematology", "Hematology", "numeric",
    ),
    (
        "CBC_MCHC", "Mean corpuscular hemoglobin concentration",
        "hematology", "Hematology", "numeric",
    ),
    (
        "CBC_PLT", "Platelet count",
        "hematology", "Hematology", "numeric",
    ),
    (
        "CHEM_CREATININE", "Creatinine",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "CHEM_UREA", "Urea",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "CHEM_BUN", "Blood urea nitrogen (BUN)",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "CHEM_SODIUM", "Sodium",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "CHEM_POTASSIUM", "Potassium",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "CHEM_CHLORIDE", "Chloride",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "CHEM_ALT", "Alanine aminotransferase (ALT)",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "CHEM_AST", "Aspartate aminotransferase (AST)",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "CHEM_ALP", "Alkaline phosphatase (ALP)",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "CHEM_GGT", "Gamma-glutamyl transferase (GGT)",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "CHEM_BILIRUBIN_TOTAL", "Bilirubin — total",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "CHEM_BILIRUBIN_DIRECT", "Bilirubin — direct",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "CHEM_ALBUMIN", "Albumin",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "CHEM_PROTEIN_TOTAL", "Protein — total",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "LIPID_CHOLESTEROL_TOTAL", "Cholesterol — total",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "LIPID_HDL", "HDL cholesterol",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "LIPID_LDL_DIRECT", "LDL cholesterol — directly measured",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "LIPID_LDL_CALCULATED", "LDL cholesterol — calculated",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "LIPID_TRIGLYCERIDES", "Triglycerides",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "GLUCOSE_FASTING", "Glucose — fasting",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "GLUCOSE_RANDOM", "Glucose — random",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "HBA1C", "Hemoglobin A1c (HbA1c)",
        "chemistry", "Chemistry", "numeric",
    ),
    (
        "THYROID_TSH", "Thyroid-stimulating hormone (TSH)",
        "endocrinology", "Endocrinology", "numeric",
    ),
    (
        "THYROID_FT4", "Thyroxine (T4) — free",
        "endocrinology", "Endocrinology", "numeric",
    ),
    (
        "THYROID_FT3", "Triiodothyronine (T3) — free",
        "endocrinology", "Endocrinology", "numeric",
    ),
    (
        "THYROID_T4_TOTAL", "Thyroxine (T4) — total",
        "endocrinology", "Endocrinology", "numeric",
    ),
    (
        "THYROID_T3_TOTAL", "Triiodothyronine (T3) — total",
        "endocrinology", "Endocrinology", "numeric",
    ),
    (
        "DIFF_NEUT_PCT", "Neutrophils — percent of leukocytes, blood",
        "hematology", "Hematology", "numeric",
    ),
    (
        "DIFF_NEUT_ABS", "Neutrophils — absolute count, blood",
        "hematology", "Hematology", "numeric",
    ),
    (
        "DIFF_LYMPH_PCT", "Lymphocytes — percent of leukocytes, blood",
        "hematology", "Hematology", "numeric",
    ),
    (
        "DIFF_LYMPH_ABS", "Lymphocytes — absolute count, blood",
        "hematology", "Hematology", "numeric",
    ),
    (
        "DIFF_MONO_PCT", "Monocytes — percent of leukocytes, blood",
        "hematology", "Hematology", "numeric",
    ),
    (
        "DIFF_MONO_ABS", "Monocytes — absolute count, blood",
        "hematology", "Hematology", "numeric",
    ),
    (
        "DIFF_EOS_PCT", "Eosinophils — percent of leukocytes, blood",
        "hematology", "Hematology", "numeric",
    ),
    (
        "DIFF_EOS_ABS", "Eosinophils — absolute count, blood",
        "hematology", "Hematology", "numeric",
    ),
    (
        "DIFF_BASO_PCT", "Basophils — percent of leukocytes, blood",
        "hematology", "Hematology", "numeric",
    ),
    (
        "DIFF_BASO_ABS", "Basophils — absolute count, blood",
        "hematology", "Hematology", "numeric",
    ),
    (
        "CBC_RDW_CV", "Red cell distribution width — CV, blood",
        "hematology", "Hematology", "numeric",
    ),
    (
        "CBC_RDW_SD", "Red cell distribution width — SD, blood",
        "hematology", "Hematology", "numeric",
    ),
    (
        "CBC_MPV", "Mean platelet volume, blood",
        "hematology", "Hematology", "numeric",
    ),
    (
        "RETIC_PCT", "Reticulocytes — percent of erythrocytes, blood",
        "hematology", "Hematology", "numeric",
    ),
    (
        "RETIC_ABS", "Reticulocytes — absolute count, blood",
        "hematology", "Hematology", "numeric",
    ),
    (
        "RETIC_IRF_PCT", "Immature reticulocyte fraction — percent of reticulocytes, blood",
        "hematology", "Hematology", "numeric",
    ),

)
