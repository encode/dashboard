from starlette.routing import Router, Route
from starlette.templating import Jinja2Templates


class Auth:
    def __init__(self):
        self.routes = [
            Route('/login', endpoint=self.login, name='login'),
            Route('/logout', endpoint=self.logout, name='logout'),
        ]
        self.router = Router(routes=self.routes)
        self.templates = Jinja2Templates(directory='templates')

    async def __call__(self, scope, receive, send) -> None:
        await self.router(scope, receive, send)

    async def login(self, request):
        template = "auth/login.html"
        context = {
            "request": request,
        }
        return self.templates.TemplateResponse(template, context)

    async def logout(self, request):
        template = "auth/login.html"
        context = {
            "request": request,
        }
        return self.templates.TemplateResponse(template, context)
