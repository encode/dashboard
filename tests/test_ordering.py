from starlette.datastructures import URL

from dashboard.ordering import ColumnControl, get_column_controls, get_ordering


def test_order_by_column():
    url = URL("?order=name")
    columns = {"name": "Name", "email": "Email"}
    ordering = get_ordering(url=url, columns=columns)
    assert ordering == "name"


def test_order_by_reverse_column():
    url = URL("?order=-name")
    columns = {"name": "Name", "email": "Email"}
    ordering = get_ordering(url=url, columns=columns)
    assert ordering == "-name"


def test_order_by_invalid_column():
    url = URL("?order=invalid")
    columns = {"name": "Name", "email": "Email"}
    ordering = get_ordering(url=url, columns=columns)
    assert ordering is None


def test_get_column_controls_no_current_selection():
    columns = {"username": "Username", "email": "Email"}
    url = URL("/")

    controls = get_column_controls(url, columns, order_by=None)

    assert controls == [
        ColumnControl(
            id="username",
            text="Username",
            url=URL("/?order=username"),
            is_forward_sorted=False,
            is_reverse_sorted=False,
        ),
        ColumnControl(
            id="email",
            text="Email",
            url=URL("/?order=email"),
            is_forward_sorted=False,
            is_reverse_sorted=False,
        ),
    ]


def test_get_column_controls_forward_current_selection():
    columns = {"username": "Username", "email": "Email"}
    url = URL("/?order=username")

    controls = get_column_controls(url, columns, order_by="username")

    assert controls == [
        ColumnControl(
            id="username",
            text="Username",
            url=URL("/?order=-username"),
            is_forward_sorted=True,
            is_reverse_sorted=False,
        ),
        ColumnControl(
            id="email",
            text="Email",
            url=URL("/?order=email"),
            is_forward_sorted=False,
            is_reverse_sorted=False,
        ),
    ]


def test_get_column_controls_reverse_current_selection():
    columns = {"username": "Username", "email": "Email"}
    url = URL("/?order=-username")

    controls = get_column_controls(url=url, columns=columns, order_by="-username")

    assert controls == [
        ColumnControl(
            id="username",
            text="Username",
            url=URL("/"),
            is_forward_sorted=False,
            is_reverse_sorted=True,
        ),
        ColumnControl(
            id="email",
            text="Email",
            url=URL("/?order=email"),
            is_forward_sorted=False,
            is_reverse_sorted=False,
        ),
    ]
