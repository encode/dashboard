from starlette.datastructures import URL

from dashboard.search import filter_by_search_term, get_search_term


def test_get_search_term():
    url = URL("?search=Email")
    assert get_search_term(url=url) == "Email"


def test_search():
    queryset = filter_by_search_term(queryset=[], search_term="")
    assert queryset == []
