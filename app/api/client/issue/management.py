import random
import string
from datetime import datetime
from pytz import timezone

from fastapi import Depends
from fastapi import APIRouter

from fastapi.responses import JSONResponse
from motor.motor_asyncio import  AsyncIOMotorDatabase

from app.api.client.issue import client_issue_router
from app.database.session import get_db

from app.utils.email_utils import notify_hod_or_club, department_hod
from app.utils.qr_utils import readb64, qr_decoder
from app.utils.issue_utils import createIssue, add_comment, resolve_issue

from app.schemas.client.issue.management import (
                                                ClientAssignIssueRequest, 
                                                ClientIssueAddCommentRequest,
                                                ClientIssueCloseRequest,
                                                ClientIssueOpenRequest,
                                                ClientIssueReportQrRequest,
                                                ClientIssueReportRequest,
                                                ClientIssueStatusRequest,
                                                ClientSimilarIssuesRequest
                                                )


client_issue_management_router =APIRouter()


@client_issue_router.post("/report", response_class=JSONResponse, tags=["Issue Management"])
async def report_issue(input_data: ClientIssueReportRequest , db:AsyncIOMotorDatabase = Depends(get_db)):
    id = input_data.id.lower()
    name = input_data.name
    issue_type = input_data.issueType
    issue_cat = input_data.issueCat
    issue_content = input_data.issueContent
    block = input_data.block
    floor = input_data.floor
    action_item = input_data.actionItem
    comments = input_data.comments
    anonymity = input_data.anonymity
    # data = input_data.model_dump()

    if not id:
        return JSONResponse({"message": "User ID is required"}, status_code=400)
    
    if not name:
        return JSONResponse({"message": "User name is required"}, status_code=400)
    
    user = await db.users.find_one({"id": id})
    if not user:
         return JSONResponse({"message": "User not found"}, status_code=404)

    survey: dict[str, str] = {}
    for k, v in input_data.model_dump().items():
        if k.startswith("survey-") and isinstance(v, str):
            survey_label = k.replace("survey-", "").replace("-", " ")
            survey_label = " ".join(word.capitalize() for word in survey_label.split(" "))
            survey[survey_label] = v
    issue_data = {
        "name": name,
        "id": id,
        "issueType": issue_type,
        "issueCat": issue_cat.upper(),
        "issueContent": issue_content,
        "block": block,
        "floor": floor,
        "actionItem": action_item,
        "comments": [{"by": id, "content": comments}],
        "survey": survey,
        "anonymity": "true" if anonymity == "on" else "false",
    }

    # issue_id = createIssue(issue_data)
    issue_id = await createIssue(issue_data, db)

    # hod_email = department_hod(user["department"])
    # notify_hod_or_club(issue_data, hod_email, user["club_email"])
    hod_email =  department_hod(user["department"])
    notify_hod_or_club(issue_data, hod_email, user["club_email"])


    return JSONResponse({"message": "Issue reported successfully", "issue_id": issue_id}, status_code=201)


@client_issue_management_router.post("/assign_issue", response_class=JSONResponse)
async def assign_issue(input_data: ClientAssignIssueRequest, db:AsyncIOMotorDatabase = Depends(get_db)):
    issue_no = input_data.issueNo
    assignee = input_data.assignee

    if not issue_no:
        return JSONResponse({"message": "Issue No is required"}, status_code=400)
    
    if not assignee:
        return JSONResponse({"message": "Assignee is required"}, status_code=400)
    
    issue = await db.dataset.find_one({"issueNo": issue_no})
    if not issue:
        return JSONResponse({"message": "Issue not found"}, status_code=404)
    
    user = await db.users.find_one({"name": assignee})
    if not user:
         return JSONResponse({"message": "Assignee not found"}, status_code=404)
    
    update_result = await db.dataset.update_one(
        {"issueNo": issue_no},
        {
            "$set": {
                "assignee": assignee
            }
        },
    )

    if update_result.modified_count > 0:
        return JSONResponse({
            "status": "success",
            "message": f"Assignee '{assignee}' has been added to issue '{issue_no}'"
        }, status_code=200)
    else:
        return JSONResponse({"message": "Failed to assign issue"}, status_code=500)
    



@client_issue_router.post("/status", response_class=JSONResponse, tags=["Issue Management"])
async def issue_status(input_data: ClientIssueStatusRequest, db:AsyncIOMotorDatabase = Depends(get_db)):
    id = input_data.user_id.lower()
    if not id:
        return JSONResponse({"status": "error", "message": "ID is required"}, status_code=400)
    
    user = await db.users.find_one({'id':id})
    if not user:
        return JSONResponse({"status": "error", "message": "User not found"}, status_code=404)
    
    issues = await db.dataset.find({'raised_by.personId': id}).to_list()
    if not issues:
        return JSONResponse({"status": "success", "data": []}, status_code=200)
    
    my_issues = []
    for i in issues:
        if (
            "issue" in i
            and "issueCat" in i["issue"]
            and "issueNo" in i
            and "status" in i
            and "date" in i
            and "issueType" in i["issue"]
            and "issueContent" in i["issue"]
        ):
            my_issues.append(
                {
                    "category": i["issue"]["issueCat"],
                    "code": i["issueNo"],
                    "status": i["status"],
                    "date": i["date"],
                    "issueType": i["issue"]["issueType"],
                    "desc": (
                        f"{i['issue']['issueContent'][:75]}..."
                        if len(i["issue"]["issueContent"]) > 75
                        else i["issue"]["issueContent"]
                    ),
                }
            )
    return JSONResponse( { "data": my_issues,"status": "success"},status_code=200 )

@client_issue_router.post("/status/{code}", response_class=JSONResponse, tags=["Issue Management"])
async def client_issue_status_description(code: str, db:AsyncIOMotorDatabase = Depends(get_db)):
    issue = await db.dataset.find_one({"issueNo": code})

    if issue:
        issue["_id"] = str(issue["_id"])
    
        # Example logic to handle anonymity based on request context (replace with your actual logic)
        if issue.get("anonymity") == "true":
            issue["raised_by"]["name"] = "Anonymous"
    
        return JSONResponse({"issue": issue})

    return JSONResponse({"message": "Issue not found"}, status_code=404)

@client_issue_router.post("/add-comment/{code}", response_class=JSONResponse, tags=["Issue Management"])
async def client_issue_add_comment(input_data: ClientIssueAddCommentRequest , code: str, db:AsyncIOMotorDatabase = Depends(get_db)):
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
    
@client_issue_router.post("/close/{code}", response_class=JSONResponse, tags=["Issue Management"])
async def client_issue_close(input_data: ClientIssueCloseRequest , code: str, db:AsyncIOMotorDatabase = Depends(get_db)):
    id = input_data.user_id.lower()
    if not id:
        return JSONResponse({"message": "User ID is required"}, status_code=400)
    
    result = await resolve_issue(code, id, "close", db)
    if result:
        return JSONResponse({"message": "Issue closed successfully"}, status_code=200)
    else:
        return JSONResponse({"message": "Failed to close issue"}, status_code=500)

@client_issue_router.post("/open/{code}", response_class=JSONResponse, tags=["Issue Management"])
async def client_issue_open(input_data: ClientIssueOpenRequest , code: str, db:AsyncIOMotorDatabase = Depends(get_db)):
    id = input_data.user_id.lower()
    if not id:
        return JSONResponse({"message": "User ID is required"}, status_code=400)
    
    result = await resolve_issue(code, id, "open", db )
    if result:
        return JSONResponse({"message": "Issue opened successfully"}, status_code=200)
    else:
        return JSONResponse({"message": "Failed to open issue"}, status_code=500)

@client_issue_router.post("/report/qr", response_class=JSONResponse, tags=["Issue Management"])
async def report_issue_qr(input_data: ClientIssueReportQrRequest , db:AsyncIOMotorDatabase = Depends(get_db)):
    id = input_data.id.lower()
    file_data = input_data.file

    if not id:
        return JSONResponse({"message": "User ID is required"}, status_code=400)
    
    if not file_data:
        return JSONResponse({"message": "File data is required"}, status_code=400)
    
    try:
        img = readb64(file_data)
        qr_result = qr_decoder(img)
        return JSONResponse({"qr_result": qr_result}, status_code=200)
    
    except Exception as e:
        return JSONResponse({"message": str(e)}, status_code=500)
    
@client_issue_management_router.post("/get_similar_issues", response_class=JSONResponse)
async def client_get_similar_issues(input_data: ClientSimilarIssuesRequest , db:AsyncIOMotorDatabase = Depends(get_db)):
    block = input_data.block
    floor = input_data.floor
    if not block:
        return JSONResponse({"message": "block is required"}, status_code=400)
    
    if not floor:
        return JSONResponse({"message": "floor data is required"}, status_code=400)
    pipeline = [
    {
        "$match": {
            "status": "OPEN",
            "issue.issueType": "Complaint",
            "issue.block": block,
            "issue.floor": floor
        }
    },
    {
        "$project": {
            "_id": 0,          # Excludes the _id field from the output
            "issueNo": 1,  # From the root document
            "time": 1,     # From the root document
            "date": 1,     # From the root document
            "name": "$raised_by.name",
            "personID": "$raised_by.personId",
            "issueCat": "$issue.issueCat",
            "issueContent": "$issue.issueContent",
            "block": "$issue.block",
            "floor": "$issue.floor",
            "actionItem": "$issue.actionItem",
            "comments": {
                "$let": {
                    "vars": {
                        "firstComment": {"$arrayElemAt": ["$comments", 0]}
                    },
                    "in": {
                        "$cond": [
                            {"$ifNull": ["$$firstComment.content", False]},
                            {
                                "$let": {
                                    "vars": {
                                        "firstContent": {"$arrayElemAt": ["$$firstComment.content", 0]}
                                    },
                                    "in": "$$firstContent.content"
                                }
                            },
                            "No comments available"
                        ]
                    }
                }
            }
        }
    }
]

    filtered_issues_cursor = db.dataset.aggregate(pipeline)
    filtered_issues = await filtered_issues_cursor.to_list(length=None)
    
    return JSONResponse(content=filtered_issues, status_code=200)

    
    



