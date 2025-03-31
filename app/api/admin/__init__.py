from fastapi import APIRouter


admin_router = APIRouter(prefix="/administrator")

from app.api.admin import administrator



