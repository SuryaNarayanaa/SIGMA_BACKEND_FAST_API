from fastapi import APIRouter
from app.api.v1.endpoints import items

api_router = APIRouter()

# Include routers from endpoints
api_router.include_router(items.router, prefix="/items", tags=["items"])

# Add more routers as your API grows
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
