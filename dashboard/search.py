import typing

from starlette.datastructures import URL, QueryParams


def get_search_term(url: URL) -> typing.Optional[str]:
    return QueryParams(url.query).get("search")


def item_matches_search(item: typing.Any, search_term: str) -> bool:
    for attribute in item.keys():
        if search_term in str(item[attribute]).lower():
            return True

    return False


def filter_by_search_term(queryset: list, search_term: str) -> list:
    if not search_term:
        return queryset

    return [
        item
        for item in queryset
        if item_matches_search(item, search_term=search_term.lower())
    ]
