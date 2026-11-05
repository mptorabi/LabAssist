from dataclasses import dataclass
from typing import Dict, Tuple

from .bundled_test_definitions import TEST_DEFINITIONS
from .bundled_units import UNIT_SUGGESTIONS


@dataclass(frozen=True)
class CatalogTest:
    code: str
    name: str
    category_code: str
    category_name: str
    input_type: str
    aliases: Tuple[str, ...] = ()
    suggested_units: Tuple[str, ...] = ()

    # Empty means unspecified, not inferred.
    specimen: str = ""
    method: str = ""
    time_aspect: str = ""

    # Exact source URLs can be recorded for reviewed definitions.
    source_urls: Tuple[str, ...] = ()


VALID_INPUT_TYPES = frozenset({
    "text",
    "numeric",
    "qualitative",
    "structured",
})


def build_catalog(panels, unit_suggestions):

    catalog: Dict[str, CatalogTest] = {}

    for (
        panel_code,
        panel_name,
        category_code,
        category_name,
        tests,
    ) in panels:
        member_codes = set()

        for code, name in tests:
            if code in member_codes:
                raise ValueError(
                    f"Duplicate test {code!r} within panel {panel_code!r}."
                )
            member_codes.add(code)

            raw_units = unit_suggestions.get(code, ())

            if not isinstance(raw_units, (tuple, list)):
                raise ValueError(
                    f"Units for {code!r} must be a tuple or list."
                )

            units = tuple(raw_units)

            if any(
                not isinstance(symbol, str) or not symbol.strip()
                for symbol in units
            ):
                raise ValueError(
                    f"Invalid or blank unit suggestion for {code!r}."
                )

            if len(units) != len(set(units)):
                raise ValueError(
                    f"Duplicate unit suggestion for {code!r}."
                )

            definition = CatalogTest(
                code=code,
                name=name,
                category_code=category_code,
                category_name=category_name,
                # Preserve the existing bundled installer definition.
                # This is not a default for future clinical additions.
                input_type="numeric",
                suggested_units=units,
            )

            existing = catalog.get(code)

            if existing is not None and existing != definition:
                raise ValueError(
                    f"Conflicting catalog definitions for {code!r}."
                )

            catalog[code] = definition

    unknown_unit_codes = set(unit_suggestions) - set(catalog)

    if unknown_unit_codes:
        raise ValueError(
            "Unit suggestions reference unknown tests: "
            + ", ".join(sorted(unknown_unit_codes))
        )

    return tuple(catalog.values())


def build_independent_catalog(definitions, unit_suggestions):
    """Validate and build tests without depending on any panel."""
    catalog = {}
    category_names = {}

    for row in definitions:
        if len(row) != 5:
            raise ValueError(
                "Each test definition must contain exactly five fields."
            )

        code, name, category_code, category_name, input_type = row

        for field_name, value in (
            ("code", code),
            ("name", name),
            ("category_code", category_code),
            ("category_name", category_name),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Invalid {field_name} in test definition."
                )

            if value != value.strip():
                raise ValueError(
                    f"Outer whitespace in {field_name} for {code!r}."
                )

        if code in catalog:
            raise ValueError(
                f"Duplicate catalog code: {code!r}."
            )

        if input_type not in VALID_INPUT_TYPES:
            raise ValueError(
                f"Invalid input type for {code!r}: {input_type!r}."
            )

        previous_category_name = category_names.get(category_code)

        if (
            previous_category_name is not None
            and previous_category_name != category_name
        ):
            raise ValueError(
                f"Conflicting names for category {category_code!r}."
            )

        category_names[category_code] = category_name

        raw_units = unit_suggestions.get(code, ())

        if not isinstance(raw_units, (tuple, list)):
            raise ValueError(
                f"Units for {code!r} must be a tuple or list."
            )

        units = tuple(raw_units)

        if any(
            not isinstance(symbol, str) or not symbol.strip()
            for symbol in units
        ):
            raise ValueError(
                f"Invalid or blank unit suggestion for {code!r}."
            )

        if len(units) != len(set(units)):
            raise ValueError(
                f"Duplicate unit suggestion for {code!r}."
            )

        catalog[code] = CatalogTest(
            code=code,
            name=name,
            category_code=category_code,
            category_name=category_name,
            input_type=input_type,
            suggested_units=units,
        )

    unknown_unit_codes = set(unit_suggestions) - set(catalog)

    if unknown_unit_codes:
        raise ValueError(
            "Unit suggestions reference unknown tests: "
            + ", ".join(sorted(unknown_unit_codes))
        )

    return tuple(catalog.values())


BUNDLED_TESTS = build_independent_catalog(
    TEST_DEFINITIONS,
    UNIT_SUGGESTIONS,
)


