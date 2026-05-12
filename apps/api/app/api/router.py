from fastapi import APIRouter

from app.api.routes import ai, imports, plans, strava, webhooks

api_router = APIRouter()
api_router.include_router(plans.router)
api_router.include_router(ai.router)
api_router.include_router(strava.router)
api_router.include_router(imports.router)
api_router.include_router(webhooks.router)
