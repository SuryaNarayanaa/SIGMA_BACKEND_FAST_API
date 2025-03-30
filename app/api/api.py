from fastapi import APIRouter
from .health import health

# Main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])

# Add more routers here as your application grows
