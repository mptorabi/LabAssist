import unittest

from labs.bundled_catalog import BUNDLED_TESTS, build_independent_catalog
from labs.bundled_panels import PANEL_DEFINITIONS
from labs.bundled_test_definitions import TEST_DEFINITIONS
from labs.bundled_units import UNIT_SUGGESTIONS


class ImmatureReticulocyteCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = {item.code: item for item in BUNDLED_TESTS}
        self.item = self.catalog["RETIC_IRF_PCT"]

    def test_identity_and_denominator(self):
        self.assertEqual(self.item.name,
                         "Immature reticulocyte fraction — percent of reticulocytes, blood")
        self.assertEqual(self.item.input_type, "numeric")
        self.assertEqual((self.item.category_code, self.item.category_name),
                         ("hematology", "Hematology"))

    def test_percentage_unit_only(self):
        self.assertEqual(self.item.suggested_units, ("%",))

    def test_separate_from_reticulocyte_percentage_and_absolute_count(self):
        items = [self.item, self.catalog["RETIC_PCT"], self.catalog["RETIC_ABS"]]
        self.assertEqual(len({item.code for item in items}), 3)
        self.assertEqual(len({item.name for item in items}), 3)
        self.assertIn("percent of erythrocytes", self.catalog["RETIC_PCT"].name)

    def test_no_inferred_metadata_or_aliases(self):
        self.assertEqual((self.item.specimen, self.item.method, self.item.time_aspect),
                         ("", "", ""))
        self.assertEqual((self.item.aliases, self.item.source_urls), ((), ()))

    def test_not_added_to_legacy_panels(self):
        members = {code for panel in PANEL_DEFINITIONS[:7] for code in panel[4]}
        self.assertNotIn(self.item.code, members)

    def test_single_definition_and_independent_build(self):
        rows = tuple(row for row in TEST_DEFINITIONS if row[0] == self.item.code)
        self.assertEqual(len(rows), 1)
        built = build_independent_catalog(rows, {
            self.item.code: UNIT_SUGGESTIONS[self.item.code],
        })
        self.assertEqual(built, (self.item,))


if __name__ == "__main__":
    unittest.main()