from fastapi import APIRouter
client_issue_router = APIRouter(prefix="/issue")

from app.api.client.issue import summary, management