from fastapi import APIRouter

manager_router = APIRouter(prefix="/manager")
from app.api.manager import auth, account, password, privileges
