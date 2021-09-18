import datetime

import pytest
import typesystem
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.testclient import TestClient

import dashboard


@pytest.fixture
def app():
    users = dashboard.MockDataSource(
        schema=typesystem.Schema(
            fields={
                "pk": typesystem.Integer(
                    title="Identity", read_only=True, default=dashboard.autoincrement()
                ),
                "username": typesystem.String(title="Username", max_length=100),
                "is_admin": typesystem.Boolean(title="Is Admin", default=False),
                "joined": typesystem.DateTime(
                    title="Joined", read_only=True, default=datetime.datetime.now
                ),
            }
        ),
        initial=[
            {
                "username": f"user{i}@example.org",
                "is_admin": False,
            }
            for i in range(100)
        ],
    )

    user_table = dashboard.DashboardTable(
        ident="users", title="Users", datasource=users
    )
    admin = dashboard.Dashboard(tables=[user_table])

    return Starlette(
        routes=[
            Mount(
                "/admin",
                admin,
                name="dashboard",
            ),
            Mount("/statics", ..., name="static"),
        ]
    )


def test_index(app):
    client = TestClient(app=app)
    response = client.get("/admin")
    assert response.status_code == 200
    assert response.template.name == "dashboard/index.html"
    assert response.context["rows"] == [
        {"text": "Users", "url": "http://testserver/admin/users/", "count": 100}
    ]


def test_table(app):
    client = TestClient(app=app)
    response = client.get("/admin/users")
    assert response.status_code == 200
    assert response.template.name == "dashboard/table.html"
    assert len(response.context["rows"]) == 10
    assert len(response.context["page_controls"]) == 10

    response = client.get("/admin/users?search=does-not-exist")
    assert response.status_code == 200
    assert response.template.name == "dashboard/table.html"
    assert len(response.context["rows"]) == 0

    response = client.get("/admin/users?search=1")
    assert response.status_code == 200
    assert response.template.name == "dashboard/table.html"
    assert len(response.context["rows"]) == 10

    response = client.get("/admin/users?order=username")
    assert response.status_code == 200
    assert response.template.name == "dashboard/table.html"
    assert response.context["rows"][0].username == "user0@example.org"

    response = client.get("/admin/users?order=-username")
    assert response.status_code == 200
    assert response.template.name == "dashboard/table.html"
    assert response.context["rows"][0].username == "user9@example.org"


def test_create(app):
    client = TestClient(app=app)
    response = client.post("/admin/users/")
    assert response.status_code == 400
    assert response.template.name == "dashboard/table.html"

    values = {"username": 101, "is_completed": False}
    response = client.post("/admin/users/", data=values, allow_redirects=True)
    assert response.status_code == 200
    assert response.url.endswith("/admin/users/")


def test_detail(app):
    client = TestClient(app=app)
    response = client.get("/admin/users/1")
    assert response.status_code == 200
    assert response.template.name == "dashboard/detail.html"

    response = client.get("/admin/users/1000")
    assert response.status_code == 404


def test_update(app):
    client = TestClient(app=app)
    response = client.post("/admin/users/1")
    assert response.status_code == 400
    assert response.template.name == "dashboard/detail.html"

    values = {"username": 1, "is_completed": False}
    response = client.post("/admin/users/1", data=values, allow_redirects=True)
    assert response.status_code == 200
    assert response.url.endswith("/admin/users/1")


def test_delete(app):
    client = TestClient(app=app)
    response = client.post("/admin/users/101/delete")
    assert response.status_code == 404

    response = client.post("/admin/users/1/delete", allow_redirects=True)
    assert response.status_code == 200
    assert response.url.endswith("/admin/users/")
