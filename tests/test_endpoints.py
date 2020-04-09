import dashboard
import typesystem
import datetime
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.testclient import TestClient
import pytest


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
            {"username": f"user{i}@example.org", "is_admin": False,} for i in range(123)
        ],
    )

    user_table = dashboard.DashboardTable(
        ident="users", title="Users", datasource=users
    )
    admin = dashboard.Dashboard(tables=[user_table])

    return Starlette(
        routes=[
            Mount("/admin", admin, name="dashboard",),
            Mount("/statics", ..., name="static"),
        ]
    )


def test_index(app):
    client = TestClient(app=app)
    response = client.get("/admin")
    assert response.status_code == 200
    assert response.template.name == "dashboard/index.html"
    assert response.context["rows"] == [
        {"text": "Users", "url": "http://testserver/admin/users/", "count": 123}
    ]
