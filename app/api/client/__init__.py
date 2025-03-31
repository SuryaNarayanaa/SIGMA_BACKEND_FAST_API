from fastapi import APIRouter

from .issue.management import client_issue_management_router
from .issue import client_issue_router

client_router = APIRouter(prefix="/client")
client_router.include_router(client_issue_router,tags=["Issues"])
client_router.include_router(client_issue_management_router)

from app.api.client import auth, account, password


