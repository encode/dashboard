import dashboard
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.testclient import TestClient


def test_index():
    app = Starlette(
        routes=[
            Mount("/admin", dashboard.Dashboard(tables=[]), name="dashboard"),
            Mount("/statics", ..., name="static"),
        ]
    )
    client = TestClient(app=app)
    response = client.get("/admin")
    assert response.status_code == 200
    assert response.template.name == "dashboard/index.html"
