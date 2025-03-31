from fastapi import APIRouter
from .health import health_router
from .client import client_router
from .tasks import tasks_router
from .lost_found import lost_and_found_router

router = APIRouter()

router.include_router(health_router,tags=["Health"])
router.include_router(client_router, tags=["Client Routes"])
router.include_router(tasks_router, tags=["Task Routes"])
router.include_router(lost_and_found_router, tags=["Lost and Found Routes"])

