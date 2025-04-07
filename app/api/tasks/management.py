from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Depends

from motor.motor_asyncio import  AsyncIOMotorDatabase

from app.database.session import get_db
from app.api.tasks import tasks_router
from app.utils.email_utils import render_template, url_for
from app.utils.issue_utils import resolve_issue, add_comment
from fastapi import Query
from app.schemas.tasks.managementSchema import (
                                                TasksIssueCloseRequest,
                                                TasksIssueOpenRequest,
                                                TasksIssueAddCommentRequest,
                                                )


@tasks_router.post("/status/{code}", response_class=JSONResponse, tags=["Task Management"])
async def issue_status_description(code: str, mod: str = None, db: AsyncIOMotorDatabase = Depends(get_db)):

    issues = await db.dataset.find({"issueNo": code}).to_list(length=None)

    if not issues:
        return JSONResponse({"message": "Issue not found"}, status_code=404)
    
    # Convert ObjectId to string for each issue and handle anonymity
    for issue in issues:
        issue["_id"] = str(issue["_id"])
        
        # Check if mod parameter is set to "1" and anonymity is "true"
        if issue.get("anonymity") == "true" and mod == "1":
            issue["anonymity"] = "false"
        
        # Apply anonymization only if still needed
        if issue.get("anonymity") == "true":
            if "raised_by" in issue and "name" in issue["raised_by"]:
                issue["raised_by"]["name"] = "Anonymous"
    
    return JSONResponse({"issues": issues}, status_code=200)

@tasks_router.post("/close/{code}", response_class=JSONResponse, tags=["Tasks Management"])
async def issue_close(input_data:TasksIssueCloseRequest, code:str, db: AsyncIOMotorDatabase = Depends(get_db)):
    id = input_data.user_id
    if not id:
        return JSONResponse({"message": "User ID is required"}, status_code=400)
    
    result = await resolve_issue(code, id, "close", db)
    if result:
        return JSONResponse({"message": "Issue closed successfully"}, status_code=200)
    else:
        return JSONResponse({"message": "Failed to close issue"}, status_code=500)

@tasks_router.post("/open/{code}", response_class=JSONResponse, tags=["Tasks Management"])
async def issue_open(input_data:TasksIssueOpenRequest, code:str, db: AsyncIOMotorDatabase = Depends(get_db)):
    id = input_data.user_id
    if not id:
        return JSONResponse({"message": "User ID is required"}, status_code=400)
    
    result = await resolve_issue(code, id, "open", db )
    if result:
        return JSONResponse({"message": "Issue opened successfully"}, status_code=200)
    else:
        return JSONResponse({"message": "Failed to open issue"}, status_code=500)

@tasks_router.post("/add-comment/{code}", response_class=JSONResponse, tags=["Tasks Management"])
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

@tasks_router.get("/export/{code}", response_class=HTMLResponse, tags=["Tasks Management"])
async def issue_status_export(code: str, mod: str = None, db: AsyncIOMotorDatabase = Depends(get_db)):

    issue = await db.dataset.find_one({"issueNo": code})

    if not issue:
        return JSONResponse({"message": "Issue not found"}, status_code=404)
    
    # Convert ObjectId to string for JSON serialization
    issue["_id"] = str(issue["_id"])

    # Check if mod parameter is set to "1" and anonymity is "true"
    if issue.get("anonymity") == "true" and mod == "1":
        issue["anonymity"] = "false"
    
    # Apply anonymization only if still needed
    if issue.get("anonymity") == "true":
        if "raised_by" in issue and "name" in issue["raised_by"]:
            issue["raised_by"]["name"] = "Anonymous"
        
    return render_template("issue_report.html", url_for=url_for, issue=issue)
