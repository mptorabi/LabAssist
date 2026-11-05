from .models import LabTest


def entry_catalog():
    tests = (LabTest.objects.filter(is_active=True)
             .select_related("category")
             .prefetch_related("aliases", "suggested_units")
             .order_by("name", "code"))
    return [
        {
            "id": str(test.pk), "code": test.code, "name": test.name,
            "category_id": str(test.category_id) if test.category_id else "",
            "category_name": test.category.name if test.category_id else "",
            "aliases": [alias.name for alias in test.aliases.all()],
            "units": [unit.symbol for unit in test.suggested_units.all() if unit.is_active],
        }
        for test in tests
    ]
