from fastapi import Depends
from fastapi.responses import JSONResponse

from app.api.client.issue import client_issue_router
from app.database.session import get_db

from motor.motor_asyncio import  AsyncIOMotorDatabase

from app.schemas.client.issue.management import IssueStatusRequest


@client_issue_router.post("/status", response_class=JSONResponse, tags=["Issue Management"])
async def issue_status(input_data: IssueStatusRequest, db:AsyncIOMotorDatabase = Depends(get_db)):
    id = input_data.id.lower()
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



"""
@app.route("/client/issue/status", methods=["POST"])
def issue_status():
    data = request.get_json()
    if not data:
        return (
            jsonify({"status": "error", "message": "Invalid or missing JSON data"}),
            400,
        )

    user_id = data.get("user_id")
    if not user_id:
        return (
            jsonify({"status": "error", "message": "Missing user_id in request data"}),
            400,
        )

    try:
        issues = mongo.db.dataset.find()
        my_issues = []
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        for i in issues:
            if i["raised_by"]["personId"] == user_id:
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
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

        return jsonify({"status": "success", "data": my_issues}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/client/issue/status/<code>", methods=["POST"])
def client_issue_status_description(code):
    return issue_status_description(code)


@app.route("/client/issue/add-comment/<code>", methods=["GET", "POST"])
def client_issue_add_comment(code):
    return issue_add_comment(code)


@app.route("/client/issue/close/<code>")
def client_issue_close(code):
    return issue_close(code)


@app.route("/client/issue/open/<code>")
def client_issue_open(code):
    return issue_open(code)
"""