import random
import string
from pytz import timezone
from datetime import datetime

from fastapi.responses import JSONResponse

from motor.motor_asyncio import  AsyncIOMotorDatabase




async def add_comment(issue_id: str, comment: dict, db:AsyncIOMotorDatabase)->bool:
    """
    addComment is a function which takes in 2 parameters, issueId and comment,
    and utilizes these parameters to search for an issue by issueId and add the comment.
    """

    right_now = datetime.now(timezone("Asia/Kolkata"))
    issue = await db.dataset.find_one({"issueNo": issue_id})

    if not issue:
        return JSONResponse({"message": "Issue not found"}, status_code=404)

    new_comment = {
        "date": datetime.now().strftime("%d-%m-%y %H:%M"),
        "by": comment["by"],
        "content": [{"by": comment["by"], "content": comment["content"]}],
    }

    update_result = await db.dataset.update_one(
        {"issueNo": issue_id},
        {
            "$push": {"comments": new_comment},
            "$set": {
                "issue.issueLastUpdateDate": right_now.strftime("%d/%m/%y"),
                "issue.issueLastUpdateTime": right_now.strftime("%I:%M %p"),
            },
        },
    )
    if update_result.modified_count > 0:
        return True
    return False


async def resolve_issue(issue_id: str, person_id: str, action: str, db:AsyncIOMotorDatabase)->bool:
    """
    resolveIssue is a function which takes in 3 parameters, issueId, personId, and action,
    and utilizes these parameters to search for an issue by issueId, mark the
    issue as either open or close, and add "opened/closed by personId" to the logs.
    """

    right_now = datetime.now(timezone("Asia/Kolkata"))

    issue = await db.dataset.find_one({"issueNo": issue_id})

    if not issue:
        return False

    right_now_str = right_now.strftime("%d-%m-%y %H:%M")
    issue_data = issue.get("issue", {})
    issue_data["issueLastUpdateDate"] = right_now.strftime("%d/%m/%y")
    issue_data["issueLastUpdateTime"] = right_now.strftime("%I:%M %p")
    
    status = "OPEN" if action.lower() == "open" else "CLOSE"
    
    update_result = await db.dataset.update_one(
        {"issueNo": issue_id},
        {
            "$push": {
                "log": {
                    "date": right_now_str,
                    "action": action,
                    "by": person_id,
                }
            },
            "$set": {
                "status": status, 
                "issue": issue_data
                },
        },
    )
    if update_result.modified_count > 0:
        return True
    return False


async def createIssue(data: dict, db: AsyncIOMotorDatabase):
    """
    the createIssue function creates an Issue and appends it to the DataBase, and takes "data",
    a dictionary as input.
    {
        "name"        : str
        "id"          : str
        "issueType"   : str
        "issueContent": str
        "block"       : str
        "floor"       : str
        "actionItem"  : str
        "comments"    : [
                          {
                            "by"      : str
                            "content" : str
                          }
                        ]
        "survey"      : {
                            "key" : str (a set of keys and values)
                        }
        "anonymity"   : str (true/false)
    }
    """

    rightNow = datetime.now(timezone("Asia/Kolkata"))
    newEntry = {
        "issueNo": "".join(random.choices(string.ascii_uppercase + string.digits, k=5)),
        "time": rightNow.strftime("%I:%M %p"),
        "date": rightNow.strftime("%d/%m/%y"),
        "ISODateTime": rightNow.isoformat(),
        "raised_by": {"name": data["name"], "personId": data["id"]},
        "issue": {
            "issueLastUpdateTime": rightNow.strftime("%I:%M %p"),
            "issueLastUpdateDate": rightNow.strftime("%d/%m/%y"),
            "issueType": data["issueType"],
            "issueCat": data["issueCat"],
            "issueContent": data["issueContent"],
            "block": data["block"],
            "floor": data["floor"],
            "actionItem": data["actionItem"],
        },
        "comments": [
            {
                "date": rightNow.strftime("%d-%m-%y %I:%M %p"),
                "by": data["comments"][0]["by"],
                "content": data["comments"][0]["content"],
            }
        ],
        "status": "OPEN",
        "log": [
            {
                "date": rightNow.strftime("%d-%m-%y %H:%M"),
                "action": "opened",
                "by": data["id"],
            }
        ],
        "survey": data["survey"],
        "anonymity": data["anonymity"],
    }

    result = await db.dataset.insert_one(newEntry)
    if result.inserted_id:
        return newEntry["issueNo"]
    else:
        return None