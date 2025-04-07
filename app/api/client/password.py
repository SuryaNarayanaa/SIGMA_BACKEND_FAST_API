import uuid

from fastapi import Depends
from fastapi import Form
from fastapi.responses import JSONResponse

from app.api.client import client_router
from app.config import settings
from app.database.session import get_db
from app.schemas.client.passwordSchema import ClientForgotPasswordRequest, ClientForgotPasswordResetRequest, ClientResetPasswordReqeust
from app.utils.email_utils import render_template, sendmail
from app.utils.password_utils import get_hash

from motor.motor_asyncio import  AsyncIOMotorDatabase


@client_router.post("/reset_password", response_class=JSONResponse, tags=["Password Management"])
async def client_reset_password(input_data: ClientResetPasswordReqeust , db: AsyncIOMotorDatabase = Depends(get_db) ):
    id = input_data.id
    old_password = input_data.old_password
    new_password = input_data.new_password

    if not id:
        return JSONResponse(
            status_code=400,
            content={"message": "ID is required"},
        )
    if not old_password:
        return JSONResponse(
            status_code=400,
            content={"message": "old password is required"},
        )
    if not new_password:
        return JSONResponse(
            status_code=400,
            content={"message": " new password is required"},
        )

    user = await db.users.find_one({"id": id})

    if not user:
        return JSONResponse(status_code=404, content={"message": "User not found"})

    if get_hash(old_password) != user["hashword"]:
        return JSONResponse(
            status_code=401, content={"message": "Old password is incorrect"}
        )

    hashed_password = get_hash(new_password)
    await db.users.update_one({"id": id}, {"$set": {"hashword": hashed_password}})

    return JSONResponse(
        status_code=200, content={"message": "Password reset successfully"}
    )

@client_router.post("/forgot_password", response_class=JSONResponse, tags=["Password Management"])
async def client_forgot_password(input_data: ClientForgotPasswordRequest , db: AsyncIOMotorDatabase = Depends(get_db) ):
    id  =input_data.id
    if not id:
        return JSONResponse(
            status_code=400,
            content={"message": "ID is required"},
        )

    user = await db.users.find_one({"id": id})

    if not user:
        return JSONResponse(status_code=404, content={"message": "User not found"})
    
    reset_key = str(uuid.uuid4()).split("-")[0].upper()
    reset_link = f"{settings.BASE_URL}/client/reset/{reset_key}"
    sendmail(
    mail_met={"type": "reset_password"},
    receiver=f"{id}",
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

    update_result = await db.users.update_one({"id": id}, {"$set": {"reset_key": reset_key}})

    if update_result.modified_count == 0:
        return JSONResponse(status_code=400, content={"message": "reset_key failed to update"})

    return JSONResponse(status_code=200, content={"message": "Please check your e-mail to reset your password."})

@client_router.get("/reset/{reset_key}" , response_class=JSONResponse, tags=["Password Management"])
async def client_reset_password_page( reset_key: str, db: AsyncIOMotorDatabase = Depends(get_db) ):
    
    user = await db.users.find_one({"reset_key": reset_key})
    if not user:
        return JSONResponse(status_code=404, content={"message": "User not found"})
    
    return render_template("reset_password.html", reset_key=reset_key)

@client_router.post("/forgot_password/reset" , response_class= JSONResponse, tags=["Password Management"])
async def client_forgot_password_reset(input_data: ClientForgotPasswordResetRequest,  db: AsyncIOMotorDatabase = Depends(get_db) ):
    reset_key = input_data.reset_key
    new_password = input_data.new_password

    user = await db.users.find_one({"reset_key": reset_key})
    if not user:
        return JSONResponse(status_code=404, content={"message": "User not found"})
    
    hashed_password = get_hash(new_password)
    
    update_result = await db.users.update_one(
        {"reset_key": reset_key},
        {"$set": {"hashword": hashed_password, "reset_key": ""}},
    )
    if update_result.modified_count == 0:
        return JSONResponse(status_code=400, content={"message": "Failed to update password"})

    return JSONResponse(status_code=200, content={"message": "Password reset successfully"})

@client_router.post("/update_password" , response_class= JSONResponse, tags=["Password Management"])
async def client_update_password(reset_key: str = Form(...), new_password: str = Form(...),  db: AsyncIOMotorDatabase = Depends(get_db) ):
    if not reset_key:
        return JSONResponse(
            status_code=400, content={"message": "Reset key is required"}
        )

    if not new_password:
        return JSONResponse(
            status_code=400, content={"message": "New password is required"}
        )

    user = await db.users.find_one({"reset_key": reset_key})

    if not user:
        return JSONResponse(status_code=400, content={"message": "Invalid or expired reset key"})

    hashed_password = get_hash(new_password)
    update_result = await db.users.update_one(
        {"reset_key": reset_key},
        {"$set": {"hashword": hashed_password, "reset_key": ""}},
    )
    
    if update_result.modified_count == 0:
        return JSONResponse(status_code=400, content={"message": "Failed to update password"})

    return JSONResponse(status_code=200, content={"message": "Password updated successfully"})
