from fastapi import Depends
from fastapi.responses import JSONResponse

from app.api.client.issue import client_issue_router
from app.database.session import get_db

from motor.motor_asyncio import  AsyncIOMotorDatabase


@client_issue_router.get("/total", response_class= JSONResponse, tags=["Issue Summary"])
async def total_issues( db: AsyncIOMotorDatabase = Depends(get_db) ):
    
    total_issues_count = await db.dataset.count_documents({})
    return JSONResponse({"total_issues": total_issues_count})


@client_issue_router.get("/total/open", response_class= JSONResponse, tags=["Issue Summary"])
async def open_issues( db: AsyncIOMotorDatabase = Depends(get_db) ):
    
    open_issues_count = await db.dataset.count_documents({"status": "OPEN"})
    return JSONResponse({"open_issues": open_issues_count})


@client_issue_router.get("/total/closed", response_class= JSONResponse, tags=["Issue Summary"])
async def closed_issues( db: AsyncIOMotorDatabase = Depends(get_db) ):
    
    closed_issues_count = await db.dataset.count_documents({"status": "CLOSE"})
    return JSONResponse({"closed_issues": closed_issues_count})




