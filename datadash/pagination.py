from dataclasses import dataclass
from starlette.datastructures import URL, QueryParams
import typing


@dataclass
class PageControl:
    text: str
    url: URL = None
    is_active: bool = False
    is_disabled: bool = False


def inclusive_range(st: int, en: int, cutoff: int) -> typing.List[int]:
    """
    Return an inclusive range from 'st' to 'en',
    bounded within a minimum of 1 and a maximum of 'cutoff'.
    """
    st = max(st, 1)
    en = min(en, cutoff)
    return list(range(st, en + 1))


def get_page_number(url: URL) -> int:
    """
    Return a page number specified in the URL query parameters.
    """
    query_params = QueryParams(url.query)
    try:
        return int(query_params.get("page", default="1"))
    except (TypeError, ValueError):
        return 1


def get_page_controls(
    url: URL, current_page: int, total_pages: int
) -> typing.List[PageControl]:
    """
    Returns a list of pagination controls, using GitHub's style for rendering
    which controls should be displayed. See eg. issue pages in GitHub.
    Previous [1] 2 3 4 5 ... 14 15 Next
    """
    assert total_pages >= 1
    assert current_page >= 1
    assert current_page <= total_pages

    # If we've only got a single page, then don't include pagination controls.
    if total_pages == 1:
        return []

    # We always have 5 contextual page numbers around the current page.
    if current_page <= 2:
        # If we're on the first or second-to-first page, then our 5 contextual
        # pages should start from the first page onwards.
        main_block = inclusive_range(1, 5, cutoff=total_pages)
    elif current_page >= total_pages - 1:
        # If we're on the last or second-to-last page, then our 5 contextual
        # pages should end with the final page backwards.
        main_block = inclusive_range(total_pages - 4, total_pages, cutoff=total_pages)
    else:
        # All other cases, our 5 contextual pages should be 2 pages on either
        # side of our current page.
        main_block = inclusive_range(
            current_page - 2, current_page + 2, cutoff=total_pages
        )

    # We always have 2 contextual page numbers at the start.
    start_block = inclusive_range(1, 2, cutoff=total_pages)
    if main_block[0] == 4:
        #  If we've only got a gap of one between the start and main blocks
        # then fill in the gap with a page marker.
        # | 1 2 3 4 5 [6] 7 8
        start_block += [3]
    elif main_block[0] > 4:
        # If we've got a gap of more that one between the start and main
        # blocks then fill in the gap with an ellipsis marker.
        # | 1 2 … 5 6 [7] 8 9
        start_block += [None]

    # We always have 2 contextual page numbers at the end.
    end_block = inclusive_range(total_pages - 1, total_pages, cutoff=total_pages)
    if main_block[-1] == total_pages - 3:
        # If we've got a gap of one between the end and main blocks then
        # fill in the gap with an page marker.
        # 92 93 [94] 95 96 97 98 99 |
        end_block = [total_pages - 2] + end_block
    elif main_block[-1] < total_pages - 3:
        # If we've got a gap of more that one between the end and main
        # blocks then fill in the gap with an ellipsis marker.
        # 91 92 [93] 94 95 … 98 99 |
        end_block = [None] + end_block

    # We've got a list of integer/None values representing which pages to
    # display in the controls. Now we use those to generate the actual
    # PageControl instances.
    seen_numbers = set()
    controls = []

    # Add a 'Previous' page control.
    if current_page == 1:
        previous_url = None
        previous_disabled = True
    elif current_page == 2:
        previous_url = url.remove_query_params("page")
        previous_disabled = False
    else:
        previous_url = url.include_query_params(page=current_page - 1)
        previous_disabled = False

    previous = PageControl(
        text="Previous", url=previous_url, is_disabled=previous_disabled
    )
    controls.append(previous)

    for page_number in start_block + main_block + end_block:
        if page_number is None:
            gap = PageControl(text="…", is_disabled=True)
            controls.append(gap)
        elif page_number not in seen_numbers:
            seen_numbers.add(page_number)
            if page_number == 1:
                page_url = url.remove_query_params("page")
            else:
                page_url = url.include_query_params(page=page_number)
            page = PageControl(
                text=str(page_number),
                url=page_url,
                is_active=page_number == current_page,
            )
            controls.append(page)

    # Add a 'Next' page control.
    if current_page == total_pages:
        next_url = None
        next_disabled = True
    else:
        next_url = url.include_query_params(page=current_page + 1)
        next_disabled = False

    next = PageControl(text="Next", url=next_url, is_disabled=next_disabled)
    controls.append(next)

    return controls
