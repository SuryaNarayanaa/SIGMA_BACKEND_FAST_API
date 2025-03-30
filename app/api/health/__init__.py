from fastapi import APIRouter
from .health import health_check_router

health_router = APIRouter()

health_router.include_router(health_check_router)

