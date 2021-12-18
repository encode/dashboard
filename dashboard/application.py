import math

import jinja2
import typesystem
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse
from starlette.routing import Mount, Route, Router
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from . import ordering, pagination, search

forms = typesystem.Jinja2Forms(directory="templates", package="dashboard")


class TableMount(Mount):
    def __init__(self, table):
        super().__init__(f"/{table.tablename}", app=table)
        self.tablename = table.tablename

    def url_path_for(self, name: str, **path_params: str):
        tablename = path_params.pop("tablename", None)
        if tablename:
            name = tablename + "_" + name
        return super().url_path_for(name, **path_params)


class Dashboard:
    def __init__(self, tables):
        statics = StaticFiles(packages=["dashboard"])
        self.routes = [
            Route("/", endpoint=self.index, name="index"),
            Mount("/statics", app=statics, name="static"),
        ] + [TableMount(table) for table in tables]
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

    def __init__(
        self, ident, title, datasource, can_create=True, can_edit=True, can_delete=True
    ):
        self.routes = [
            Route("/", endpoint=self.table, name=f"{ident}_table", methods=["GET"]),
            Route("/", endpoint=self.create, name=f"{ident}_create", methods=["POST"]),
            Route(
                "/{ident}",
                endpoint=self.detail,
                name=f"{ident}_detail",
                methods=["GET"],
            ),
            Route(
                "/{ident}", endpoint=self.edit, name=f"{ident}_edit", methods=["POST"]
            ),
            Route(
                "/{ident}/delete",
                endpoint=self.delete,
                name=f"{ident}_delete",
                methods=["POST"],
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
        self.can_create = can_create
        self.can_edit = can_edit
        self.can_delete = can_delete

    async def __call__(self, scope, receive, send) -> None:
        await self.router(scope, receive, send)

    async def table(self, request):
        template = "dashboard/table.html"

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
            url=request.url,
            columns=columns,
            order_by=order_by,
        )
        page_controls = pagination.get_page_controls(
            url=request.url, current_page=current_page, total_pages=total_pages
        )

        form = forms.create_form(schema=datasource.schema)
        context = self._context(
            form=form,
            request=request,
            rows=rows,
            column_controls=column_controls,
            page_controls=page_controls,
            search_term=search_term,
        )

        return self.templates.TemplateResponse(template, context, status_code=200)

    async def create(self, request):
        template = "dashboard/table.html"

        if not self.can_create:
            raise HTTPException(status_code=401)

        form = forms.create_form(schema=self.datasource.schema)
        data = await request.form()
        form.validate(data)
        if form.is_valid:
            await self.datasource.create(**form.validated_data)
            return RedirectResponse(url=request.url, status_code=303)

        context = self._context(form=form, request=request)

        return self.templates.TemplateResponse(template, context, status_code=400)

    async def detail(self, request):
        template = "dashboard/detail.html"

        item = await self._get_item(request)

        form = forms.create_form(schema=self.datasource.schema, values=item)
        context = self._context(form=form, item=item, request=request)

        return self.templates.TemplateResponse(template, context, status_code=200)

    async def edit(self, request):
        template = "dashboard/detail.html"

        if not self.can_edit:
            raise HTTPException(status_code=401)

        item = await self._get_item(request)

        form = forms.create_form(schema=self.datasource.schema, values=item)
        data = await request.form()
        form.validate(data)
        if form.is_valid:
            await item.update(**form.validated_data)
            return RedirectResponse(url=request.url, status_code=303)

        context = self._context(form=form, item=item, request=request)
        return self.templates.TemplateResponse(template, context, status_code=400)

    async def delete(self, request):
        if not self.can_delete:
            raise HTTPException(status_code=401)

        item = await self._get_item(request)

        await item.delete()

        url = request.url_for("dashboard:table", tablename=self.tablename)
        return RedirectResponse(url=url, status_code=303)

    def _context(self, form, request, **kwargs):
        base_context = {
            "form": form,
            "request": request,
            "schema": self.datasource.schema,
            "title": self.title,
            "tablename": self.tablename,
            "lookup_field": self.LOOKUP_FIELD,
            "can_create": self.can_create,
            "can_edit": self.can_edit,
            "can_delete": self.can_delete,
        }
        return {**base_context, **kwargs}

    async def _get_item(self, request):
        ident = request.path_params["ident"]
        lookup = {self.LOOKUP_FIELD: ident}

        item = await self.datasource.filter(**lookup).get()
        if item is None:
            raise HTTPException(status_code=404)

        return item
