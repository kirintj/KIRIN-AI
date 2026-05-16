from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from tortoise import Tortoise

from app.core.bootstrap import make_middlewares, register_exceptions, register_routers
from app.core.seed import init_data
from app.services.upload_service import AVATAR_DIR, UPLOAD_DIR, STATIC_DIR
from app.services.health import get_health_checker
from app.services.registry import get_registry
from app.settings.config import settings


def _register_health_checks():
    """注册基础健康检查"""
    checker = get_health_checker()

    async def check_db():
        try:
            await Tortoise.get_connection("default").execute_query("SELECT 1")
            return True, "ok"
        except Exception as e:
            return False, str(e)[:100]

    checker.register_check("database", check_db)
    checker.register_check("app", lambda: (True, "ok"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    await init_data()
    _register_health_checks()
    yield
    await Tortoise.close_connections()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.VERSION,
        openapi_url="/openapi.json",
        middleware=make_middlewares(),
        lifespan=lifespan,
    )
    register_exceptions(app)
    register_routers(app, prefix="/api")
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    return app


app = create_app()
