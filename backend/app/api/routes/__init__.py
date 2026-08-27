"""API router aggregation for THE JUNCTION backend."""

from fastapi import APIRouter

from app.api.routes import analysis, health

api_router = APIRouter(prefix="/api")

api_router.include_router(health.router)
api_router.include_router(analysis.router)