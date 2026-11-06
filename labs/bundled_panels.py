from .bundled_catalog import BUNDLED_TESTS


# Fields:
# panel_code, panel_name, category_code, category_name, test_codes

PANEL_DEFINITIONS = (
    (
        "builtin-cbc",
        "CBC — basic indices (no differential)",
        "hematology",
        "Hematology",
        (
            "CBC_WBC",
            "CBC_RBC",
            "CBC_HGB",
            "CBC_HCT",
            "CBC_MCV",
            "CBC_MCH",
            "CBC_MCHC",
            "CBC_PLT",
        ),
    ),
    (
        "builtin-renal",
        "Renal markers — creatinine and urea",
        "chemistry",
        "Chemistry",
        (
            "CHEM_CREATININE",
            "CHEM_UREA",
            "CHEM_BUN",
        ),
    ),
    (
        "builtin-electrolytes",
        "Electrolytes — basic",
        "chemistry",
        "Chemistry",
        (
            "CHEM_SODIUM",
            "CHEM_POTASSIUM",
            "CHEM_CHLORIDE",
        ),
    ),
    (
        "builtin-liver",
        "Liver-related markers",
        "chemistry",
        "Chemistry",
        (
            "CHEM_ALT",
            "CHEM_AST",
            "CHEM_ALP",
            "CHEM_GGT",
            "CHEM_BILIRUBIN_TOTAL",
            "CHEM_BILIRUBIN_DIRECT",
            "CHEM_ALBUMIN",
            "CHEM_PROTEIN_TOTAL",
        ),
    ),
    (
        "builtin-lipids",
        "Lipid markers",
        "chemistry",
        "Chemistry",
        (
            "LIPID_CHOLESTEROL_TOTAL",
            "LIPID_HDL",
            "LIPID_LDL_DIRECT",
            "LIPID_LDL_CALCULATED",
            "LIPID_TRIGLYCERIDES",
        ),
    ),
    (
        "builtin-glycemia",
        "Glucose and HbA1c",
        "chemistry",
        "Chemistry",
        (
            "GLUCOSE_FASTING",
            "GLUCOSE_RANDOM",
            "HBA1C",
        ),
    ),
    (
        "builtin-thyroid",
        "Thyroid markers",
        "endocrinology",
        "Endocrinology",
        (
            "THYROID_TSH",
            "THYROID_FT4",
            "THYROID_FT3",
            "THYROID_T4_TOTAL",
            "THYROID_T3_TOTAL",
        ),
    ),
    ('builtin-cbc-extended', 'CBC — extended indices (no differential)', 'hematology', 'Hematology', ('CBC_WBC', 'CBC_RBC', 'CBC_HGB', 'CBC_HCT', 'CBC_MCV', 'CBC_MCH', 'CBC_MCHC', 'CBC_PLT', 'CBC_RDW_CV', 'CBC_RDW_SD', 'CBC_MPV')),
    ('builtin-differential-percent', 'Leukocyte differential — percentages', 'hematology', 'Hematology', ('DIFF_NEUT_PCT', 'DIFF_LYMPH_PCT', 'DIFF_MONO_PCT', 'DIFF_EOS_PCT', 'DIFF_BASO_PCT')),
    ('builtin-differential-absolute', 'Leukocyte differential — absolute counts', 'hematology', 'Hematology', ('DIFF_NEUT_ABS', 'DIFF_LYMPH_ABS', 'DIFF_MONO_ABS', 'DIFF_EOS_ABS', 'DIFF_BASO_ABS')),
    ('builtin-reticulocytes', 'Reticulocytes — reported parameters', 'hematology', 'Hematology', ('RETIC_PCT', 'RETIC_ABS', 'RETIC_IRF_PCT')),
    ('builtin-coagulation', 'Coagulation — PT, INR and aPTT', 'coagulation', 'Coagulation', ('COAG_PT', 'COAG_INR', 'COAG_APTT')),
    ('builtin-minerals', 'Minerals — reported blood measurements', 'chemistry', 'Chemistry', ('CHEM_CALCIUM_TOTAL', 'CHEM_CALCIUM_IONIZED', 'CHEM_MAGNESIUM', 'CHEM_PHOSPHATE')),
    ('builtin-iron', 'Iron-related measurements', 'chemistry', 'Chemistry', ('IRON_SERUM', 'IRON_FERRITIN', 'IRON_TIBC', 'IRON_TRANSFERRIN')),
)


def build_legacy_panels(definitions, catalog):
    """Resolve code references into the existing installer format."""
    tests_by_code = {}

    for test in catalog:
        if test.code in tests_by_code:
            raise ValueError(
                f"Duplicate catalog code: {test.code!r}."
            )
        tests_by_code[test.code] = test

    panels = []
    panel_codes = set()

    for (
        panel_code,
        panel_name,
        category_code,
        category_name,
        test_codes,
    ) in definitions:
        if panel_code in panel_codes:
            raise ValueError(
                f"Duplicate panel code: {panel_code!r}."
            )
        panel_codes.add(panel_code)

        members = []
        seen = set()

        for test_code in test_codes:
            if test_code in seen:
                raise ValueError(
                    f"Duplicate test {test_code!r} "
                    f"within panel {panel_code!r}."
                )
            seen.add(test_code)

            if test_code not in tests_by_code:
                raise ValueError(
                    f"Unknown test {test_code!r} "
                    f"in panel {panel_code!r}."
                )

            test = tests_by_code[test_code]

            # The legacy installer uses the panel category for tests.
            # Reject mixed-category panels until that installer is updated.
            if (
                test.category_code != category_code
                or test.category_name != category_name
            ):
                raise ValueError(
                    f"Category mismatch for {test_code!r} "
                    f"in panel {panel_code!r}."
                )

            members.append((test.code, test.name))

        panels.append(
            (
                panel_code,
                panel_name,
                category_code,
                category_name,
                tuple(members),
            )
        )

    return tuple(panels)


PANELS = build_legacy_panels(PANEL_DEFINITIONS, BUNDLED_TESTS)


DESCRIPTION = (
    "Entry preset only, not a recommendation to order tests or a complete laboratory panel. "
    "Enter only tests explicitly present on your report. Leave other rows entirely blank. "
    "Copy units and reference ranges from the report; do not infer them. "
    "Use an exact measurement match (for example urea vs BUN, free vs total, "
    "or direct vs calculated). If uncertain, do not substitute another test."
)
