"""THE JUNCTION - FastAPI application entrypoint.

Module layout:
    app/config.py          -> settings + data directory bootstrap
    app/api/routes/        -> HTTP route handlers (health, analysis, ...)
    app/core/              -> domain services (tracking, risk, ...)
    app/services/          -> scheduled jobs / workers
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import api_router, health, analysis
from app.config import settings
from app.db.database import init_db

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered road conflict intelligence for CCTV traffic footage.",
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Mount /api routes as well as root fallbacks for maximum frontend compatibility
app.include_router(api_router)
app.include_router(health.router)
app.include_router(analysis.router)


@app.get("/", include_in_schema=False)
def root() -> JSONResponse:
    return JSONResponse(
        {
            "service": settings.app_name,
            "tagline": "Predicting danger before it becomes an accident.",
            "docs": "/docs",
            "health": "/api/health",
        }
    )