from dataclasses import FrozenInstanceError

from django.test import SimpleTestCase

from .bundled_catalog import (
    BUNDLED_TESTS,
    VALID_INPUT_TYPES,
    CatalogTest,
    build_catalog,
    build_independent_catalog
)
from .bundled_panels import PANELS, build_legacy_panels
from .bundled_units import UNIT_SUGGESTIONS


class BundledCatalogTests(SimpleTestCase):
    def make_panel(self, code, tests):
        return (
            code,
            "Synthetic panel",
            "synthetic",
            "Synthetic",
            tests,
        )

    def test_current_catalog_preserves_all_legacy_tests(self):
        expected = {
            code: name
            for panel in PANELS
            for code, name in panel[4]
        }
        actual = {
            test.code: test.name
            for test in BUNDLED_TESTS
        }

        self.assertEqual(len(actual), len(BUNDLED_TESTS))
        self.assertTrue(set(expected).issubset(actual))

        for code, name in expected.items():
            with self.subTest(code=code):
                self.assertEqual(actual[code], name)

    def test_current_categories_and_input_types_are_preserved(self):
        catalog = {
            test.code: test
            for test in BUNDLED_TESTS
        }

        for _, _, category_code, category_name, tests in PANELS:
            for code, _ in tests:
                with self.subTest(code=code):
                    definition = catalog[code]
                    self.assertEqual(
                        definition.category_code,
                        category_code,
                    )
                    self.assertEqual(
                        definition.category_name,
                        category_name,
                    )
                    self.assertEqual(
                        definition.input_type,
                        "numeric",
                    )
                    self.assertIn(
                        definition.input_type,
                        VALID_INPUT_TYPES,
                    )

    def test_current_unit_spellings_and_order_are_preserved(self):
        for test in BUNDLED_TESTS:
            with self.subTest(code=test.code):
                self.assertEqual(
                    test.suggested_units,
                    UNIT_SUGGESTIONS.get(test.code, ()),
                )

    def test_unknown_metadata_is_not_inferred(self):
        for test in BUNDLED_TESTS:
            with self.subTest(code=test.code):
                self.assertEqual(test.specimen, "")
                self.assertEqual(test.method, "")
                self.assertEqual(test.time_aspect, "")
                self.assertEqual(test.aliases, ())
                self.assertEqual(test.source_urls, ())

    def test_same_test_can_belong_to_multiple_panels(self):
        panels = (
            self.make_panel(
                "synthetic-a",
                (("SYN_SHARED", "Synthetic shared test"),),
            ),
            self.make_panel(
                "synthetic-b",
                (("SYN_SHARED", "Synthetic shared test"),),
            ),
        )

        catalog = build_catalog(panels, {})

        self.assertEqual(len(catalog), 1)
        self.assertEqual(catalog[0].code, "SYN_SHARED")

    def test_duplicate_within_one_panel_is_rejected(self):
        panels = (
            self.make_panel(
                "synthetic-a",
                (
                    ("SYN_A", "Synthetic test"),
                    ("SYN_A", "Synthetic test"),
                ),
            ),
        )

        with self.assertRaisesRegex(ValueError, "Duplicate test"):
            build_catalog(panels, {})

    def test_conflicting_names_are_rejected(self):
        panels = (
            self.make_panel(
                "synthetic-a",
                (("SYN_SHARED", "Synthetic first identity"),),
            ),
            self.make_panel(
                "synthetic-b",
                (("SYN_SHARED", "Synthetic different identity"),),
            ),
        )

        with self.assertRaisesRegex(
            ValueError,
            "Conflicting catalog definitions",
        ):
            build_catalog(panels, {})

    def test_missing_unit_mapping_is_allowed(self):
        panels = (
            self.make_panel(
                "synthetic-a",
                (("SYN_A", "Synthetic unitless test"),),
            ),
        )

        catalog = build_catalog(panels, {})

        self.assertEqual(catalog[0].suggested_units, ())

    def test_units_for_unknown_test_are_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "unknown tests",
        ):
            build_catalog(
                (),
                {"SYN_UNKNOWN": ("demo/L",)},
            )

    def test_invalid_unit_suggestions_are_rejected(self):
        panels = (
            self.make_panel(
                "synthetic-a",
                (("SYN_A", "Synthetic test"),),
            ),
        )

        invalid_values = (
            "demo/L",
            ("",),
            ("   ",),
            (None,),
            ("demo/L", "demo/L"),
        )

        for units in invalid_values:
            with self.subTest(units=units):
                with self.assertRaises(ValueError):
                    build_catalog(
                        panels,
                        {"SYN_A": units},
                    )

    def test_definition_is_immutable(self):
        definition = CatalogTest(
            code="SYN_A",
            name="Synthetic test",
            category_code="synthetic",
            category_name="Synthetic",
            input_type="qualitative",
        )

        with self.assertRaises(FrozenInstanceError):
            setattr(definition, "name", "Changed")
class IndependentCatalogTests(SimpleTestCase):
    def make_definition(self, code="SYN_A", input_type="numeric"):
        return (
            code,
            "Synthetic test",
            "synthetic",
            "Synthetic",
            input_type,
        )

    def make_panel(self, panel_code, test_codes):
        return (
            panel_code,
            "Synthetic panel",
            "synthetic",
            "Synthetic",
            test_codes,
        )

    def test_test_can_exist_without_any_panel(self):
        catalog = build_independent_catalog(
            (self.make_definition(),),
            {},
        )

        self.assertEqual(len(catalog), 1)
        self.assertEqual(catalog[0].code, "SYN_A")
        self.assertEqual(build_legacy_panels((), catalog), ())

    def test_non_numeric_test_keeps_explicit_input_type(self):
        catalog = build_independent_catalog(
            (self.make_definition(input_type="qualitative"),),
            {},
        )

        self.assertEqual(catalog[0].input_type, "qualitative")
        self.assertEqual(catalog[0].suggested_units, ())

    def test_duplicate_catalog_definition_is_rejected(self):
        definition = self.make_definition()

        with self.assertRaisesRegex(
            ValueError,
            "Duplicate catalog code",
        ):
            build_independent_catalog(
                (definition, definition),
                {},
            )

    def test_invalid_input_type_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Invalid input type"):
            build_independent_catalog(
                (self.make_definition(input_type="invalid"),),
                {},
            )

    def test_unknown_unit_code_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown tests"):
            build_independent_catalog(
                (self.make_definition(),),
                {"SYN_UNKNOWN": ("demo/L",)},
            )

    def test_unit_spelling_and_order_are_preserved(self):
        catalog = build_independent_catalog(
            (self.make_definition(),),
            {"SYN_A": ("demo/L", "demo/mL")},
        )

        self.assertEqual(
            catalog[0].suggested_units,
            ("demo/L", "demo/mL"),
        )

    def test_invalid_units_are_rejected(self):
        for units in (
            "demo/L",
            ("",),
            (" ",),
            (None,),
            ("demo/L", "demo/L"),
        ):
            with self.subTest(units=units):
                with self.assertRaises(ValueError):
                    build_independent_catalog(
                        (self.make_definition(),),
                        {"SYN_A": units},
                    )

    def test_shared_membership_is_allowed(self):
        catalog = build_independent_catalog(
            (self.make_definition(),),
            {},
        )
        definitions = (
            self.make_panel("synthetic-a", ("SYN_A",)),
            self.make_panel("synthetic-b", ("SYN_A",)),
        )

        panels = build_legacy_panels(definitions, catalog)

        self.assertEqual(len(panels), 2)
        self.assertEqual(
            panels[0][4],
            (("SYN_A", "Synthetic test"),),
        )
        self.assertEqual(panels[0][4], panels[1][4])

    def test_unknown_panel_member_is_rejected(self):
        definitions = (
            self.make_panel("synthetic-a", ("SYN_UNKNOWN",)),
        )

        with self.assertRaisesRegex(ValueError, "Unknown test"):
            build_legacy_panels(definitions, ())

    def test_duplicate_member_within_panel_is_rejected(self):
        catalog = build_independent_catalog(
            (self.make_definition(),),
            {},
        )
        definitions = (
            self.make_panel("synthetic-a", ("SYN_A", "SYN_A")),
        )

        with self.assertRaisesRegex(ValueError, "Duplicate test"):
            build_legacy_panels(definitions, catalog)

    def test_duplicate_panel_code_is_rejected(self):
        panel = self.make_panel("synthetic-a", ())

        with self.assertRaisesRegex(ValueError, "Duplicate panel code"):
            build_legacy_panels((panel, panel), ())

    def test_legacy_adapter_rejects_category_mismatch(self):
        catalog = build_independent_catalog(
            (self.make_definition(),),
            {},
        )
        definitions = (
            (
                "synthetic-a",
                "Synthetic panel",
                "other",
                "Other",
                ("SYN_A",),
            ),
        )

        with self.assertRaisesRegex(ValueError, "Category mismatch"):
            build_legacy_panels(definitions, catalog)
