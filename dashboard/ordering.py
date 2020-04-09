from dataclasses import dataclass
from starlette.datastructures import URL, QueryParams
import typing


@dataclass
class ColumnControl:
    id: str
    text: str
    url: URL = None
    is_forward_sorted: bool = False
    is_reverse_sorted: bool = False

    @property
    def is_sorted(self):
        return self.is_forward_sorted or self.is_reverse_sorted


def get_ordering(url: URL, columns: typing.Dict[str, str]) -> typing.Optional[str]:
    """
    Determine a column ordering based on the URL query string.
    """
    query_params = QueryParams(url.query)
    order_by = query_params.get("order")
    if order_by is not None and order_by.lstrip("-") not in columns:
        return None
    return order_by


def get_column_controls(
    url: URL, columns: typing.Dict[str, str], order_by: typing.Optional[str],
) -> typing.List[ColumnControl]:
    selected_column = None if order_by is None else order_by.lstrip("-")
    is_reverse = order_by is not None and order_by.startswith("-")

    controls = []
    for column_id, name in columns.items():

        if selected_column != column_id:
            # Column is not selected. Link URL to forward search.
            linked_url = url.include_query_params(order=column_id).remove_query_params(
                "page"
            )
        elif not is_reverse:
            # Column is selected as a forward search. Link URL to reverse search.
            linked_url = url.include_query_params(
                order="-" + column_id
            ).remove_query_params("page")
        else:
            # Column is selected as a reverse search. Link URL to remove search.
            linked_url = url.remove_query_params("order").remove_query_params("page")

        control = ColumnControl(
            id=column_id,
            text=name,
            url=linked_url,
            is_forward_sorted=selected_column == column_id and not is_reverse,
            is_reverse_sorted=selected_column == column_id and is_reverse,
        )
        controls.append(control)
    return controls
