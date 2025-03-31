
from datetime import datetime, timedelta
from io import BytesIO

from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import JSONResponse, Response

from app.api.manager import manager_router
from app.database.session import get_db
from motor.motor_asyncio import  AsyncIOMotorDatabase
from app.schemas.accountSchema import DeleteUserRequest, UserBase, DateRangeParams,UserAccountRequest
from app.utils.pdf_utils import generate_pdf_utility

# Endpoints
@manager_router.post("/delete")
async def manager_delete(request: DeleteUserRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    user_id = request.id.lower()
    
    if not user_id:
        return JSONResponse(content={"message": "ID required"}, status_code=400)
    
    user = await db.personnel.find_one({"id": user_id})
    
    if not user:
        return JSONResponse(content={"message": "User not found"}, status_code=404)
    
    await db.personnel.delete_one({"id": user_id})
    
    return JSONResponse(content={"message": "User deleted successfully"}, status_code=200)

@manager_router.get("/pending-approval", response_class=JSONResponse)
async def get_pending_approval_users(db: AsyncIOMotorDatabase = Depends(get_db)):
    pending_users_cursor = db.personnel.find({"confirmed": True, "approved": False})
    pending_users = []
    pending_users_list = await pending_users_cursor.to_list(length=None)
    pending_users = [
        UserBase(
            name=user["name"],
            id=user["id"],
            confirmed=user["confirmed"],
            approved=user["approved"],
            confkey=user["confkey"],
            modkey=user["modkey"]
        )
        for user in pending_users_list
    ]
    
    pending_count = len(pending_users)
    return JSONResponse(content={"count": pending_count, "users": pending_users}, status_code=200)

@manager_router.post("/account")
async def account_page(request: UserAccountRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    user_id = request.id
    
    if not user_id:
        return JSONResponse(content={"message": "ID is required"}, status_code=400)
    
    user = await db.personnel.find_one({"id": user_id})
    
    if not user:
        return JSONResponse(content={"message": "Invalid ID"}, status_code=401)
    
    # Convert ObjectId to string for JSON serialization
    user["_id"] = str(user["_id"])
    return JSONResponse(content={"user": user}, status_code=200)

@manager_router.get('/generate-pdf', response_class=Response, responses={
    200: {"description": "PDF report generated successfully", "content": {"application/pdf": {}}},
    400: {"description": "Invalid date format"},
    404: {"description": "No available issues in the given date range"}
})
async def generate_pdf(params: DateRangeParams = Depends(), db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        # Convert input date strings to datetime objects
        from_date = datetime.strptime(params.from_date, "%d-%m-%Y")
        to_date = datetime.strptime(params.to_date, "%d-%m-%Y")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use 'DD-MM-YYYY'.")

    # Adjust `to_date` to include the entire day
    to_date = to_date + timedelta(days=1) - timedelta(seconds=1)

    # Fetch data and calculate metrics directly in MongoDB when possible
    pipeline = [
        {
            "$match": {
                "ISODateTime": {
                    "$gte": from_date.isoformat(),
                    "$lte": to_date.isoformat(),
                }
            }
        }
    ]

    result = await db.dataset.aggregate(pipeline).to_list(length=None)
 

    # Process aggregated result

    buffer = await generate_pdf_utility(from_date, to_date, result,db)
    return Response(buffer.getvalue(), 
                    media_type="application/pdf", 
                    headers={"Content-Disposition": "inline;filename=dynamic_report.pdf"})









"""
@manager_router.get('/generate-pdf')
async def generate_pdf(params: DateRangeParams = Depends(), db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        # Convert input date strings to datetime objects
        from_date = datetime.strptime(params.from_date, "%d-%m-%Y")
        to_date = datetime.strptime(params.to_date, "%d-%m-%Y")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use 'DD-MM-YYYY'.")

    # Adjust `to_date` to include the entire day
    to_date = to_date + timedelta(days=1) - timedelta(seconds=1)

    # Fetch data from the MongoDB collection within the date range
    pipeline = [
        {
            "$match": {
                "ISODateTime": {
                    "$gte": from_date.isoformat(),
                    "$lte": to_date.isoformat(),
                }
            }
        },
        {
            "$project": {
                "status": 1,
                "issue.issueCat": 1,
                "log": 1,
            }
        }
    ]

    issues = await db.dataset.aggregate(pipeline).to_list(length=None)

    # Check if the issues list is empty
    if not issues:
        raise HTTPException(status_code=404, detail="No available issues in the given range.")

    # Initialize counters and accumulators
    total_days = 0
    closed_issues_count = 0
    open_issues_count = 0
    total_close_time = 0
    complaint_categories = {}

    for issue in issues:
        try:
            # Extract issue details
            status = issue.get("status")
            category = issue.get("issue", {}).get("issueCat", "Unknown")
            logs = issue.get("log", [])

            # Count open and closed issues
            if status == "CLOSE":
                closed_issues_count += 1
            elif status == "OPEN":
                open_issues_count += 1

            # Calculate the most common category
            complaint_categories[category] = complaint_categories.get(category, 0) + 1

            # Calculate total days from logs and closing times
            if logs:
                start_date = datetime.strptime(logs[0]["date"], "%d-%m-%y %H:%M")
                close_dates = [
                    datetime.strptime(log["date"], "%d-%m-%y %H:%M")
                    for log in logs
                    if log["action"] == "closed"
                ]
                if close_dates:
                    total_days += (close_dates[-1] - start_date).days
                    total_close_time += sum(
                        (close_date - start_date).days for close_date in close_dates
                    )
        except Exception as e:
            print(f"Error processing issue {issue.get('_id')}: {e}")

    # Compute metrics
    total_issues = closed_issues_count + open_issues_count
    avg_close_time = total_close_time / closed_issues_count if closed_issues_count > 0 else 0
    most_common_category = max(complaint_categories, key=complaint_categories.get) if complaint_categories else "N/A"

    # Create PDF with computed metrics
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, f"Report from {params.from_date} to {params.to_date}")
    c.drawString(100, 730, f"Total Issues: {total_issues}")
    c.drawString(100, 710, f"Closed Issues: {closed_issues_count}")
    c.drawString(100, 690, f"Open Issues: {open_issues_count}")
    c.drawString(100, 670, f"Average Close Time (days): {avg_close_time:.2f}")
    c.drawString(100, 650, f"Most Common Category: {most_common_category}")
    c.save()
    buffer.seek(0)
    
    return Response(buffer.getvalue(), 
                    media_type="application/pdf", 
                    headers={"Content-Disposition": "inline;filename=dynamic_report.pdf"})"""