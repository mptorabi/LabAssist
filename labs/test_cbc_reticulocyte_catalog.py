import unittest

from labs.bundled_catalog import BUNDLED_TESTS, build_independent_catalog
from labs.bundled_panels import PANEL_DEFINITIONS
from labs.bundled_test_definitions import TEST_DEFINITIONS
from labs.bundled_units import UNIT_SUGGESTIONS


EXPECTED = {
    "CBC_RDW_CV": ("Red cell distribution width — CV, blood", ("%",)),
    "CBC_RDW_SD": ("Red cell distribution width — SD, blood", ("fL",)),
    "CBC_MPV": ("Mean platelet volume, blood", ("fL",)),
    "RETIC_PCT": ("Reticulocytes — percent of erythrocytes, blood", ("%",)),
    "RETIC_ABS": ("Reticulocytes — absolute count, blood", ("x 10(9)/L",)),
}


class CBCReticulocyteCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = {item.code: item for item in BUNDLED_TESTS}

    def test_exact_names_units_and_types(self):
        for code, (name, units) in EXPECTED.items():
            with self.subTest(code=code):
                item = self.catalog[code]
                self.assertEqual((item.name, item.suggested_units), (name, units))
                self.assertEqual(item.input_type, "numeric")
                self.assertEqual((item.category_code, item.category_name),
                                 ("hematology", "Hematology"))

    def test_five_unique_identities(self):
        rows = [row for row in TEST_DEFINITIONS if row[0] in EXPECTED]
        self.assertEqual(len(rows), 5)
        self.assertEqual(len({row[1] for row in rows}), 5)

    def test_no_inferred_metadata_or_aliases(self):
        for code in EXPECTED:
            item = self.catalog[code]
            self.assertEqual((item.specimen, item.method, item.time_aspect), ("", "", ""))
            self.assertEqual((item.aliases, item.source_urls), ((), ()))

    def test_not_added_to_legacy_panels(self):
        members = {code for panel in PANEL_DEFINITIONS[:7] for code in panel[4]}
        self.assertTrue(set(EXPECTED).isdisjoint(members))

    def test_basic_cbc_unchanged(self):
        cbc = next(panel for panel in PANEL_DEFINITIONS if panel[0] == "builtin-cbc")
        self.assertEqual(cbc[4], ("CBC_WBC", "CBC_RBC", "CBC_HGB", "CBC_HCT",
                                  "CBC_MCV", "CBC_MCH", "CBC_MCHC", "CBC_PLT"))

    def test_new_batch_builds_without_panels(self):
        rows = tuple(row for row in TEST_DEFINITIONS if row[0] in EXPECTED)
        units = {code: UNIT_SUGGESTIONS[code] for code in EXPECTED}
        self.assertEqual({t.code for t in build_independent_catalog(rows, units)}, set(EXPECTED))

    def test_ambiguous_and_calculated_codes_not_added(self):
        for code in ("RDW", "RETIC", "RETIC_CORRECTED", "RPI", "IRF"):
            self.assertNotIn(code, self.catalog)


if __name__ == "__main__":
    unittest.main()
