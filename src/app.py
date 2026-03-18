from __future__ import annotations

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

# local imports
from src.config import config
from src.database import connect_db, close_db
from src.routers.pin_router import pin_route
from src.routers.auth_router import auth_route
from src.routers.user_router import user_route
from src.routers.vault_router import vault_route
from src.routers.journal_router import journal_route
from src.routers.watchlist_router import watchlist_route
from src.routers.newsletter_router import newsletter_route


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    root_path=config.ROOT_PATH,
    description=config.APP_DESC,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS.split(",") if config.CORS_ORIGINS else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    return {"status": "ok"}


app.include_router(auth_route, prefix="/api/auth", tags=["Authentication"])
app.include_router(user_route, prefix="/api/user", tags=["Users"])
app.include_router(pin_route, prefix="/api/pin", tags=["Pin"])
app.include_router(vault_route, prefix="/api/vault", tags=["Vault"])
app.include_router(journal_route, prefix="/api/journal", tags=["Journal"])
app.include_router(watchlist_route, prefix="/api/watchlist", tags=["Watchlist"])
app.include_router(newsletter_route, prefix="/api/newsletter", tags=["Newsletter"])


def custom_swagger_ui() -> dict:
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=config.APP_NAME,
        version=config.APP_VERSION,
        description=config.APP_DESC,
        routes=app.routes,
    )
    base_server_url = config.ROOT_PATH or "/"
    openapi_schema["servers"] = [{"url": base_server_url}]
    components = openapi_schema.setdefault("components", {})
    components.setdefault("securitySchemes", {})["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    openapi_schema.setdefault("security", []).append({"BearerAuth": []})
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_swagger_ui
