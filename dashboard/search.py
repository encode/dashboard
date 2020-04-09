from starlette.datastructures import URL, QueryParams
import typing


def get_search_term(url: URL) -> typing.Optional[str]:
    return QueryParams(url.query).get("search")


def item_matches_search(
    item: typing.Any, search_term: str, attributes: typing.Sequence[str]
) -> bool:
    for attribute in attributes:
        if search_term in str(item[attribute]).lower():
            return True

    return False


def filter_by_search_term(
    queryset: list, search_term: str, attributes: typing.Sequence[str]
) -> list:
    if not search_term:
        return queryset

    return [
        item
        for item in queryset
        if item_matches_search(
            item, search_term=search_term.lower(), attributes=attributes
        )
    ]
