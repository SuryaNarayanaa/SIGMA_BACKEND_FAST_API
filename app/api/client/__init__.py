from fastapi import APIRouter
from .issue import client_issue_router

client_router = APIRouter(prefix="/client")
client_router.include_router(client_issue_router,tags=["Issues"])

from app.api.client import auth, account, password

