"""Bounded search input shared by record-list views."""


def search_query(request):
    return request.GET.get("q", "").strip()[:200]
