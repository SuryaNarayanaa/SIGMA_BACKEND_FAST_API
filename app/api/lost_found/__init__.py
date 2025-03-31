from fastapi import APIRouter

lost_and_found_router = APIRouter()
from app.api.lost_found import lost_and_found
