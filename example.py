from starlette.applications import Starlette
from starlette.config import Config
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from datadash import Auth, Dashboard, Datasource
import os


config = Config()
SECRET_KEY = config('SECRET_KEY', cast=str, default='123')
HTTPS_ONLY = config('HTTPS_ONLY', cast=bool, default=False)

templates = Jinja2Templates(directory='templates')
statics = StaticFiles(directory='statics')
dashboard = Dashboard(datasources={
    "users": Datasource(title="Users"),
    "migrations": Datasource(title="Migrations"),
    "log-records": Datasource(title="Log Records")
})
auth = Auth()


routes = [
    Mount("/dashboard", app=dashboard, name='dashboard'),
    Mount("/auth", app=auth, name='auth'),
    Mount("/statics", app=statics, name='static')
]

middleware = [
    Middleware(SessionMiddleware, secret_key=SECRET_KEY, https_only=HTTPS_ONLY)
]

app = Starlette(debug=True, routes=routes, middleware=middleware)
