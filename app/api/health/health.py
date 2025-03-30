from fastapi import APIRouter, Depends
from app.database.session import get_db

health_check_router = APIRouter(prefix="/health")

@health_check_router.get("/")
async def health_check(db=Depends(get_db)):
    """
    Health check endpoint to verify API and database connectivity.
    """
    try:
        await db.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "service": "SIGMA API",
        "version": "1.0.0",
        "database": db_status
    }
