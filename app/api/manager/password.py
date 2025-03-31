import uuid

from fastapi import Depends
from fastapi import HTTPException, Form
from fastapi.responses import HTMLResponse

from motor.motor_asyncio import  AsyncIOMotorDatabase

from app.config import settings
from app.api.manager import manager_router
from app.database.session import get_db
from app.utils.password_utils import get_hash
from app.utils.email_utils import render_template, sendmail
from app.schemas.manager.loginSchema import(
                                        ResetPasswordRequest,
                                        ForgotPasswordRequest,
                                        ForgotPasswordResetRequest
                                    )



# Define Pydantic models for request data validation


@manager_router.post("/reset_password", tags = ["Manager - Password Management"])
async def manager_reset_password(
    request: ResetPasswordRequest, 
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await db.personnel.find_one({"id": request.id.lower()})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if get_hash(request.old_password) != user["hashword"]:
        raise HTTPException(status_code=401, detail="Old password is incorrect")

    hashed_password = get_hash(request.new_password)
    await db.personnel.update_one(
        {"id": request.id}, 
        {"$set": {"hashword": hashed_password}}
    )

    return {"message": "Password reset successfully"}

@manager_router.post("/forgot_password",  tags = ["Manager - Password Management"])
async def manager_forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user_id = request.id.lower()
    user = await db.personnel.find_one({"id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_key = str(uuid.uuid4()).split("-")[0].upper()
    reset_link = f"{settings.BASE_URL}/manager/reset/{reset_key}"
    
    await sendmail(
        mail_met={"type": "reset_password"},
        receiver=f"{user_id}@psgtech.ac.in",
        subject="[PSG-GMS-SIGMA] Reset Your Password",
        short_subject="Reset Your Password",
        text=f"""Dear {user['name']},
        <br/>We received a request to reset your password. Please click the link below to reset your password.
        <br/><br/>
        <a style="text-decoration:none;background-color: #2A4BAA;font-size: 20px;border: none;color: white;border-radius: 10px;padding-top: 10px;padding-bottom: 10px;padding-left: 30px;padding-right: 30px;" href="{reset_link}">Reset Password</a>
        <br/><br/>
        If the button does not work, please visit {reset_link} and reset your password.
        <br/>Thank You.""",
    )

    await db.personnel.update_one({"id": user_id}, {"$set": {"reset_key": reset_key}})
    return {"message": "Please check your e-mail to reset your password."}

@manager_router.post("/forgot_password/reset",  tags = ["Manager - Password Management"])
async def manager_forgot_password_reset(
    request: ForgotPasswordResetRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    reset_key = request.reset_key.upper()
    user = await db.personnel.find_one({"reset_key": reset_key})

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset key")
    
    hashed_password = get_hash(request.new_password)
    await db.personnel.update_one(
        {"reset_key": reset_key}, 
        {"$set": {"hashword": hashed_password}}
    )
    return {"message": "Password reset successfully"}

@manager_router.get("/reset/{reset_key}", response_class=HTMLResponse ,  tags = ["Manager - Password Management"])
async def manager_reset_password_page(
    reset_key: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await db.personnel.find_one({"reset_key": reset_key})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset key")
    return render_template("mgr_reset_password.html", reset_key=reset_key)

@manager_router.post("/update_password",  tags = ["Manager - Password Management"])
async def manager_update_password(
    reset_key: str = Form(...),
    new_password: str = Form(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await db.personnel.find_one({"reset_key": reset_key})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset key")

    hashed_password = get_hash(new_password)
    await db.personnel.update_one(
        {"reset_key": reset_key},
        {"$set": {"hashword": hashed_password, "reset_key": ""}}
    )
    return {"message": "Password updated successfully"}