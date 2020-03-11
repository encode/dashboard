from starlette.exceptions import HTTPException
from starlette.routing import Router, Route
from starlette.templating import Jinja2Templates
import math
from . import ordering, pagination, search
from .datasource import Datasource


class Dashboard:
    PAGE_SIZE = 10
    LOOKUP_FIELD = 'pk'

    def __init__(self):
        self.routes = [
            Route('/', endpoint=self.index, name='index'),
            Route('/{tablename}', endpoint=self.table, name='table'),
            Route('/{tablename}/{ident}', endpoint=self.detail, name='detail'),
        ]
        self.router = Router(routes=self.routes)
        self.templates = Jinja2Templates(directory='templates')
        self.datasources = {
            "users": Datasource(title="Users"),
            "migrations": Datasource(title="Migrations"),
            "log-records": Datasource(title="Log Records")
        }

    async def __call__(self, scope, receive, send) -> None:
        await self.router(scope, receive, send)

    async def index(self, request):
        template = "dashboard/index.html"
        rows = [
            {
                "text": datasource.title,
                "url": request.url_for('dashboard:table', tablename=key),
                "count": await datasource.count(),
            } for key, datasource in self.datasources.items()
        ]
        context = {
            "request": request,
            "rows": rows,
        }
        return self.templates.TemplateResponse(template, context)

    async def table(self, request):
        template = "dashboard/table.html"
        tablename = request.path_params["tablename"]

        datasource = self.datasources[tablename]

        columns = {key: field.title for key, field in datasource.schema.fields.items()}

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
            datasource = datasource.order_by(order_by=order_column, reverse=is_reverse)

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
            "schema": datasource.schema,
            "title": datasource.title,
            "form_errors": {},
            "form_values": {},
            "tablename": request.path_params["tablename"],
            "rows": rows,
            "column_controls": column_controls,
            "page_controls": page_controls,
            "view_style": view_style,
            "lookup_field": self.LOOKUP_FIELD
        }
        return self.templates.TemplateResponse(template, context)

    async def detail(self, request):
        template = "dashboard/detail.html"

        tablename = request.path_params["tablename"]
        ident = request.path_params["ident"]

        datasource = self.datasources[tablename]

        ident = datasource.schema.fields[self.LOOKUP_FIELD].validate(ident)
        lookup = {self.LOOKUP_FIELD: ident}
        item = await datasource.get(**lookup)
        if item is None:
            raise HTTPException(status_code=404)

        view_style = request.query_params.get("view")
        if view_style not in ("json", "table"):
            view_style = "table"

        # Render the page
        context = {
            "request": request,
            "schema": datasource.schema,
            "title": datasource.title,
            "tablename": tablename,
            "item": item,
            "form_values": {},
            "form_errors": {},
            "view_style": view_style,
            "lookup_field": self.LOOKUP_FIELD
        }
        return self.templates.TemplateResponse(template, context)
