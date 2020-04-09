from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
import databases
import dashboard
import orm
import datetime


database = databases.Database('sqlite:///test.db')
models = orm.ModelRegistry(database=database)
templates = Jinja2Templates(directory='templates')
statics = StaticFiles(directory='statics')


class Notes(orm.Model):
    registry = models
    tablename = 'notes'
    fields = {
        'id': orm.Integer(title="ID", primary_key=True, read_only=True),
        'created': orm.DateTime(title="Created", default=datetime.datetime.now, read_only=True),
        'text': orm.String(title="Text", max_length=100),
        'completed': orm.Boolean(title="Completed", default=False)
    }


admin = dashboard.Dashboard(tables=[
    dashboard.DashboardTable(ident="users", title="Users", datasource=dashboard.Datasource()),
    dashboard.DashboardTable(ident="notes", title="Notes", datasource=Notes.objects.order_by('-id')),
])
auth = dashboard.Auth()


routes = [
    Mount("/admin", app=admin, name='dashboard'),
    Mount("/auth", app=auth, name='auth'),
    Mount("/statics", app=statics, name='static')
]

app = Starlette(debug=True, routes=routes, on_startup=[database.connect], on_shutdown=[database.disconnect])
