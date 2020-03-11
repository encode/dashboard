from starlette.routing import Router, Route
from starlette.templating import Jinja2Templates
import typesystem
import math
from . import ordering, pagination, search
from .datasource import Datasource


class User(typesystem.Schema):
    username = typesystem.String(title="Username", max_length=100)
    is_admin = typesystem.Boolean(title="Is Admin")
    joined = typesystem.DateTime(title="Joined")


class Dashboard:
    PAGE_SIZE = 10

    def __init__(self):
        self.routes = [
            Route('/', endpoint=self.index, name='index'),
            Route('/{tablename}', endpoint=self.table, name='table'),
        ]
        self.router = Router(routes=self.routes)
        self.templates = Jinja2Templates(directory='templates')

    async def __call__(self, scope, receive, send) -> None:
        await self.router(scope, receive, send)

    async def index(self, request):
        template = "dashboard/index.html"
        rows = [
            {"text": "Users", "url": request.url_for('dashboard:table', tablename='users'), "count": 5},
            {"text": "Migrations", "url": request.url_for('dashboard:table', tablename='migrations'), "count": 20},
            {"text": "Log Records", "url": request.url_for('dashboard:table', tablename='log-records'), "count": 2406},
        ]
        context = {
            "request": request,
            "rows": rows,
        }
        return self.templates.TemplateResponse(template, context)

    async def table(self, request):
        template = "dashboard/table.html"
        schema = User

        columns = {key: field.title for key, field in schema.fields.items()}
        datasource = Datasource()

        # Get some normalised information from URL query parameters
        current_page = pagination.get_page_number(url=request.url)
        order_column, is_reverse = ordering.get_ordering(url=request.url, columns=columns)
        search_term = search.get_search_term(url=request.url)

        # Filter by any search term
        datasource = datasource.search(search_term)

        # Determine pagination info
        count = await datasource.count()
        total_pages = max(math.ceil(count / self.PAGE_SIZE), 1)
        current_page = max(min(current_page, total_pages), 1)
        offset = (current_page - 1) * self.PAGE_SIZE

        # Perform column ordering
        if order_column is not None:
            datasource = datasource.order_by(column=order_column, reverse=is_reverse)

        #  Perform pagination
        datasource = datasource.offset(offset).limit(self.PAGE_SIZE)
        rows = await datasource.all()

        # Get pagination and column controls to render on the page
        column_controls = ordering.get_column_controls(
            url=request.url,
            columns=columns,
            selected_column=order_column,
            is_reverse=is_reverse,
        )
        page_controls = pagination.get_page_controls(
            url=request.url, current_page=current_page, total_pages=total_pages
        )

        view_style = request.query_params.get("view")
        if view_style not in ("json", "table"):
            view_style = "table"

        context = {
            "request": request,
            "schema": schema,
            "form_errors": {},
            "form_values": {},
            "tablename": request.path_params["tablename"],
            "rows": rows,
            "column_controls": column_controls,
            "page_controls": page_controls,
            "view_style": view_style
        }
        return self.templates.TemplateResponse(template, context)
