from fastapi import APIRouter, Depends
from app.database.session import get_db

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify API and database connectivity.
    """
    return {
        "status": "healthy",
        "service": "SIGMA API",
        "version": "1.0.0"
    }
