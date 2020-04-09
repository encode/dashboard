from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse
from starlette.routing import Router, Route, Mount, NoMatchFound
from starlette.templating import Jinja2Templates
import math
import typesystem
import jinja2
from . import ordering, pagination, search
from .datasource import DataSource


forms = typesystem.Jinja2Forms(directory="templates", package="dashboard")


class TableMount(Mount):
    def __init__(self, table):
        super().__init__(f"/{table.tablename}", app=table)
        self.tablename = table.tablename

    def url_path_for(self, name: str, **path_params: str):
        tablename = path_params.pop("tablename", None)
        if tablename != self.tablename:
            raise NoMatchFound()
        return super().url_path_for(name, **path_params)


class Dashboard:
    def __init__(self, tables):
        self.routes = [Route("/", endpoint=self.index, name="index"),] + [
            TableMount(table) for table in tables
        ]
        self.router = Router(routes=self.routes)
        self.templates = Jinja2Templates(directory="templates")
        self.templates.env.loader = jinja2.ChoiceLoader(
            [
                jinja2.FileSystemLoader("templates"),
                jinja2.PackageLoader("dashboard", "templates"),
            ]
        )
        self.tables = tables

    async def __call__(self, scope, receive, send) -> None:
        await self.router(scope, receive, send)

    async def index(self, request):
        template = "dashboard/index.html"
        rows = [
            {
                "text": table.title,
                "url": request.url_for("dashboard:table", tablename=table.tablename),
                "count": await table.datasource.count(),
            }
            for table in self.tables
        ]
        context = {
            "request": request,
            "rows": rows,
        }
        return self.templates.TemplateResponse(template, context)


class DashboardTable:
    PAGE_SIZE = 10
    LOOKUP_FIELD = "pk"

    def __init__(self, ident, title, datasource):
        self.routes = [
            Route("/", endpoint=self.table, name="table", methods=["GET", "POST"]),
            Route(
                "/{ident}", endpoint=self.detail, name="detail", methods=["GET", "POST"]
            ),
            Route(
                "/{ident}/delete", endpoint=self.delete, name="delete", methods=["POST"]
            ),
        ]
        self.router = Router(routes=self.routes)
        self.templates = Jinja2Templates(directory="templates")
        self.templates.env.loader = jinja2.ChoiceLoader(
            [
                jinja2.FileSystemLoader("templates"),
                jinja2.PackageLoader("dashboard", "templates"),
            ]
        )
        self.title = title
        self.tablename = ident
        self.datasource = datasource

    async def __call__(self, scope, receive, send) -> None:
        await self.router(scope, receive, send)

    async def table(self, request):
        template = "dashboard/table.html"

        tablename = self.tablename
        datasource = self.datasource

        columns = {key: field.title for key, field in datasource.schema.fields.items()}

        # Get some normalised information from URL query parameters
        current_page = pagination.get_page_number(url=request.url)
        order_by = ordering.get_ordering(url=request.url, columns=columns)
        search_term = search.get_search_term(url=request.url)

        # Filter by any search term
        if search_term:
            datasource = datasource.search(search_term)

        # Determine pagination info
        count = await datasource.count()
        total_pages = max(math.ceil(count / self.PAGE_SIZE), 1)
        current_page = max(min(current_page, total_pages), 1)
        offset = (current_page - 1) * self.PAGE_SIZE

        # Perform column ordering
        if order_by is not None:
            datasource = datasource.order_by(order_by=order_by)

        #  Perform pagination
        datasource = datasource.offset(offset).limit(self.PAGE_SIZE)
        rows = await datasource.all()

        # Get pagination and column controls to render on the page
        column_controls = ordering.get_column_controls(
            url=request.url, columns=columns, order_by=order_by,
        )
        page_controls = pagination.get_page_controls(
            url=request.url, current_page=current_page, total_pages=total_pages
        )

        form = forms.create_form(schema=datasource.schema)
        if request.method == "POST":
            data = await request.form()
            form.validate(data)
            if form.is_valid:
                await datasource.create(**form.validated_data)
                return RedirectResponse(url=request.url, status_code=303)
            status_code = 400
        else:
            status_code = 200

        context = {
            "request": request,
            "schema": datasource.schema,
            "title": self.title,
            "form": form,
            "tablename": self.tablename,
            "rows": rows,
            "column_controls": column_controls,
            "page_controls": page_controls,
            "lookup_field": self.LOOKUP_FIELD,
            "can_edit": True,
            "search_term": search_term,
        }
        return self.templates.TemplateResponse(
            template, context, status_code=status_code
        )

    async def detail(self, request):
        template = "dashboard/detail.html"

        tablename = self.tablename
        datasource = self.datasource

        ident = request.path_params["ident"]

        lookup = {self.LOOKUP_FIELD: ident}
        item = await datasource.filter(**lookup).get()
        if item is None:
            raise HTTPException(status_code=404)

        form = forms.create_form(schema=datasource.schema, instance=item)
        if request.method == "POST":
            data = await request.form()
            form.validate(data)
            if form.is_valid:
                await item.update(**form.validated_data)
                return RedirectResponse(url=request.url, status_code=303)
            status_code = 400
        else:
            status_code = 200

        # Render the page
        context = {
            "request": request,
            "schema": datasource.schema,
            "title": self.title,
            "tablename": tablename,
            "item": item,
            "form": form,
            "lookup_field": self.LOOKUP_FIELD,
            "can_edit": True,
        }
        return self.templates.TemplateResponse(
            template, context, status_code=status_code
        )

    async def delete(self, request):
        tablename = self.tablename
        datasource = self.datasource

        ident = request.path_params["ident"]

        lookup = {self.LOOKUP_FIELD: ident}
        item = await datasource.filter(**lookup).get()
        if item is None:
            raise HTTPException(status_code=404)

        await item.delete()

        url = request.url_for("dashboard:table", tablename=tablename)
        return RedirectResponse(url=url, status_code=303)
