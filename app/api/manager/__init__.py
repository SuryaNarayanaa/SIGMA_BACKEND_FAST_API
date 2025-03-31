from fastapi import APIRouter

manager_router = APIRouter(prefix="/manager")
from app.api.manager import auth, login, account, password, privileges
