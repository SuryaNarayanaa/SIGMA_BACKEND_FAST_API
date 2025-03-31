from fastapi import APIRouter
from .health import health_router
from .client import client_router
from .tasks import task_router

router = APIRouter()

router.include_router(health_router,tags=["Health"])
router.include_router(client_router, tags=["Client Routes"])
router.include_router(task_router, tags=["Task Routes"])

