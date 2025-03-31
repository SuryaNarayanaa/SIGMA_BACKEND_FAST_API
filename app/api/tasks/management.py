from fastapi.responses import JSONResponse
from fastapi import Depends

from datetime import datetime, timedelta
from motor.motor_asyncio import  AsyncIOMotorDatabase

from app.database.session import get_db
from app.api.tasks import tasks_router
from app.utils.issue_utils import resolve_issue, add_comment
from app.schemas.tasks.managementSchema import (
                                                TasksIssueCloseRequest,
                                                TasksIssueOpenRequest,
                                                TasksIssueAddCommentRequest,
                                                )
@tasks_router.get("/close/{code}", response_class=JSONResponse, tags=["Tasks Management"])
async def issue_close(input_data:TasksIssueCloseRequest, code:str, db: AsyncIOMotorDatabase = Depends(get_db)):
    id = input_data.user_id.lower()
    if not id:
        return JSONResponse({"message": "User ID is required"}, status_code=400)
    
    result = await resolve_issue(code, id, "close", db)
    if result:
        return JSONResponse({"message": "Issue closed successfully"}, status_code=200)
    else:
        return JSONResponse({"message": "Failed to close issue"}, status_code=500)

@tasks_router.get("/open/{code}", response_class=JSONResponse, tags=["Tasks Management"])
async def issue_open(input_data:TasksIssueOpenRequest, code:str, db: AsyncIOMotorDatabase = Depends(get_db)):
    id = input_data.user_id.lower()
    if not id:
        return JSONResponse({"message": "User ID is required"}, status_code=400)
    
    result = await resolve_issue(code, id, "open", db )
    if result:
        return JSONResponse({"message": "Issue opened successfully"}, status_code=200)
    else:
        return JSONResponse({"message": "Failed to open issue"}, status_code=500)

@tasks_router.get("/add-comment/{code}", response_class=JSONResponse, tags=["Tasks Management"])
async def issue_add_comment(input_data:TasksIssueAddCommentRequest, code:str, db: AsyncIOMotorDatabase = Depends(get_db)):
    id = input_data.user_id.lower()
    content = input_data.content

    if not id:
        return JSONResponse({"message": "User ID is required"}, status_code=400)
    if not content:
        return JSONResponse({"message": "Comment content is required"}, status_code=400)

    result = await add_comment(code, {"content": content, "by": id}, db)
    if result:
        return JSONResponse({"message": "Comment added successfully"}, status_code=200)
    else:
        return JSONResponse({"message": "Failed to add comment"}, status_code=500)
