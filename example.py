from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import RedirectResponse
import databases
import dashboard
import orm
import datetime


database = databases.Database("sqlite:///test.db")
models = orm.ModelRegistry(database=database)


class Notes(orm.Model):
    registry = models
    tablename = "notes"
    fields = {
        "id": orm.Integer(title="ID", primary_key=True),
        "created": orm.DateTime(
            title="Created", default=datetime.datetime.now, read_only=True
        ),
        "text": orm.String(title="Text", max_length=100),
        "completed": orm.Boolean(title="Completed", default=False),
    }


admin = dashboard.Dashboard(
    tables=[
        dashboard.DashboardTable(
            ident="notes",
            title="Notes",
            datasource=Notes.objects.order_by("-id"),
        ),
    ]
)


routes = [
    Mount("/admin", app=admin, name="dashboard"),
    Route("/", endpoint=RedirectResponse(url="/admin")),
]

app = Starlette(
    debug=True,
    routes=routes,
    on_startup=[database.connect],
    on_shutdown=[database.disconnect],
)
