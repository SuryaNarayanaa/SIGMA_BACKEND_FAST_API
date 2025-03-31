from fastapi import Depends
from fastapi.responses import HTMLResponse

from app.api.manager import manager_router
from app.database.session import get_db

from app.utils.email_utils import render_template, sendmail

from motor.motor_asyncio import  AsyncIOMotorDatabase


@manager_router.get("/escalate/{modkey}")
async def manager_escalate_email(modkey: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    # Find user with the given modkey
    user_to_escalate = await db.personnel.find_one({"modkey": modkey})
    
    if not user_to_escalate:
        return HTMLResponse(
            content=render_template(
                "response.html",
                message="Invalid moderator key"
            ),
            status_code=400
        )
    
    # Check if the user is already a moderator
    if user_to_escalate.get("mod") == 1:
        return HTMLResponse(
            content=render_template(
                "response.html",
                message="User is already a moderator"
            ),
            status_code=200
        )
    
    # Update user to be a moderator
    await db.personnel.update_one(
        {"_id": user_to_escalate.get("_id")},
        {"$set": {"confirmed": True, "approved": True, "mod": 1}},
    )
    
    id = user_to_escalate["id"]
    name = user_to_escalate["name"]
    
    # Send email notification
    sendmail(
        {"type": "welcome"},
        f"{id}@psgtech.ac.in",
        "[PSG-GMS-SIGMA] Privileges Escalated to Moderator Status!",
        "Congrats! You have been Assigned to Moderator Status with Account Approval Privileges!",
        f"""Dear {name},
        <br/>Welcome to "SIGMA" General Maintenance Software by PSG College of Technology! You have been Assigned to Moderator Status with Account Approval Privileges! You will now be notified via e-mail whenever someone creates a new account, and be responsible for approval of new accounts!
        <br/>Thank You.""",
    )
    
    return HTMLResponse(
        content=render_template(
            "response.html",
            message="You have escalated this user's privileges to moderator status."
        ),
        status_code=200
    )
