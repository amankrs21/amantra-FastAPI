from __future__ import annotations

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

# local imports
from src.config import config
from src.database import connect_db, close_db
from src.routers.auth_router import auth_route


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


# Intialize FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    root_path=config.ROOT_PATH,
    description=config.APP_DESC,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS.split(",") if config.CORS_ORIGINS else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    return {"status": "ok"}


# Route inclusion
app.include_router(auth_route, prefix="/api/auth", tags=["Authentication"])
# app.include_router(user.router, prefix="/api", tags=["Users"])
# app.include_router(vault.router, prefix="/api", tags=["Vault"])
# app.include_router(journal.router, prefix="/api", tags=["Journal"])
# app.include_router(pin.router, prefix="/api", tags=["Pin"])
# app.include_router(watchlist.router, prefix="/api", tags=["Watchlist"])
# app.include_router(newsletter.router, prefix="/api", tags=["Newsletter"])


# Swagger UI customization
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

# Set custom OpenAPI schema
app.openapi = custom_swagger_ui
