from starlette.datastructures import URL

from dashboard.pagination import PageControl, get_page_controls, get_page_number


def test_single_page_does_not_include_any_pagination_controls():
    """
    When there is only a single page, no pagination controls should render.
    """
    url = URL("/")
    controls = get_page_controls(url, current_page=1, total_pages=1)
    assert controls == []


def test_first_page_in_pagination_controls():
    """
    First page in pagination controls, should render as:
    Previous [1] 2 3 4 5 Next
    """
    url = URL("/")
    controls = get_page_controls(url, current_page=1, total_pages=5)
    assert controls == [
        PageControl(text="Previous", is_disabled=True),
        PageControl(text="1", is_active=True, url=URL("/")),
        PageControl(text="2", url=URL("/?page=2")),
        PageControl(text="3", url=URL("/?page=3")),
        PageControl(text="4", url=URL("/?page=4")),
        PageControl(text="5", url=URL("/?page=5")),
        PageControl(text="Next", url=URL("/?page=2")),
    ]


def test_second_page_in_pagination_controls():
    """
    Second page in pagination controls, should render as:
    Previous 1 [2] 3 4 5 Next
    """
    url = URL("/")
    controls = get_page_controls(url, current_page=2, total_pages=5)
    assert controls == [
        PageControl(text="Previous", url=URL("/")),  # No query parameter needed.
        PageControl(text="1", url=URL("/")),
        PageControl(text="2", is_active=True, url=URL("/?page=2")),
        PageControl(text="3", url=URL("/?page=3")),
        PageControl(text="4", url=URL("/?page=4")),
        PageControl(text="5", url=URL("/?page=5")),
        PageControl(text="Next", url=URL("/?page=3")),
    ]


def test_middle_page_in_pagination_controls():
    """
    Middle page in pagination controls, should render as:
    Previous 1 2 [3] 4 5 Next
    """
    url = URL("/?page=3")
    controls = get_page_controls(url, current_page=3, total_pages=5)
    assert controls == [
        PageControl(text="Previous", url=URL("/?page=2")),
        PageControl(text="1", url=URL("/")),
        PageControl(text="2", url=URL("/?page=2")),
        PageControl(text="3", is_active=True, url=URL("/?page=3")),
        PageControl(text="4", url=URL("/?page=4")),
        PageControl(text="5", url=URL("/?page=5")),
        PageControl(text="Next", url=URL("/?page=4")),
    ]


def test_last_page_in_pagination_controls():
    """
    Last page in pagination controls, should render as:
    Previous 1 2 3 4 [5] Next
    """
    url = URL("/?page=5")
    controls = get_page_controls(url, current_page=5, total_pages=5)
    assert controls == [
        PageControl(text="Previous", url=URL("/?page=4")),
        PageControl(text="1", url=URL("/")),
        PageControl(text="2", url=URL("/?page=2")),
        PageControl(text="3", url=URL("/?page=3")),
        PageControl(text="4", url=URL("/?page=4")),
        PageControl(text="5", url=URL("/?page=5"), is_active=True),
        PageControl(text="Next", is_disabled=True),
    ]


def test_first_page_in_long_pagination_controls():
    """
    First page in long pagination controls, should render as:
    Previous [1] 2 3 4 5 ... 49 50 Next
    """
    url = URL("/")
    controls = get_page_controls(url, current_page=1, total_pages=50)
    assert controls == [
        PageControl(text="Previous", is_disabled=True),
        PageControl(text="1", is_active=True, url=URL("/")),
        PageControl(text="2", url=URL("/?page=2")),
        PageControl(text="3", url=URL("/?page=3")),
        PageControl(text="4", url=URL("/?page=4")),
        PageControl(text="5", url=URL("/?page=5")),
        PageControl(text="…", is_disabled=True),
        PageControl(text="49", url=URL("/?page=49")),
        PageControl(text="50", url=URL("/?page=50")),
        PageControl(text="Next", url=URL("/?page=2")),
    ]


def test_last_page_in_long_pagination_controls():
    """
    Last page in long pagination controls, should render as:
    Previous 1 2 ... 46 47 48 49 [50] Next
    """
    url = URL("/?page=50")
    controls = get_page_controls(url, current_page=50, total_pages=50)
    assert controls == [
        PageControl(text="Previous", url=URL("/?page=49")),
        PageControl(text="1", url=URL("/")),
        PageControl(text="2", url=URL("/?page=2")),
        PageControl(text="…", is_disabled=True),
        PageControl(text="46", url=URL("/?page=46")),
        PageControl(text="47", url=URL("/?page=47")),
        PageControl(text="48", url=URL("/?page=48")),
        PageControl(text="49", url=URL("/?page=49")),
        PageControl(text="50", is_active=True, url=URL("/?page=50")),
        PageControl(text="Next", is_disabled=True),
    ]


def test_ellipsis_fill_in():
    """
    If an ellipsis marker can be replaced with a single page marker, then
    we should do so.
    """
    url = URL("/?page=6")
    controls = get_page_controls(url, current_page=6, total_pages=11)
    assert controls == [
        PageControl(text="Previous", url=URL("/?page=5")),
        PageControl(text="1", url=URL("/")),
        PageControl(text="2", url=URL("/?page=2")),
        PageControl(text="3", url=URL("/?page=3")),  # Ellipsis fill-in case.
        PageControl(text="4", url=URL("/?page=4")),
        PageControl(text="5", url=URL("/?page=5")),
        PageControl(text="6", url=URL("/?page=6"), is_active=True),
        PageControl(text="7", url=URL("/?page=7")),
        PageControl(text="8", url=URL("/?page=8")),
        PageControl(text="9", url=URL("/?page=9")),  # Ellipsis fill-in case.
        PageControl(text="10", url=URL("/?page=10")),
        PageControl(text="11", url=URL("/?page=11")),
        PageControl(text="Next", url=URL("/?page=7")),
    ]


def test_default_page_number():
    url = URL("/")
    page = get_page_number(url=url)
    assert page == 1


def test_explicit_page_number():
    url = URL("/?page=2")
    page = get_page_number(url=url)
    assert page == 2


def test_invalid_page_number():
    url = URL("/?page=invalid")
    page = get_page_number(url=url)
    assert page == 1
