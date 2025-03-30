from fastapi import APIRouter
client_router = APIRouter(prefix="/client")
from app.api.client import auth, account, password

