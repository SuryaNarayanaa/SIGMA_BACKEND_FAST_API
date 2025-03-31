import uuid
from fastapi import Depends
from fastapi.responses import HTMLResponse, JSONResponse

from app.config import settings
from app.api.manager import manager_router
from app.database.session import get_db

from app.utils.password_utils import get_hash
from app.utils.email_utils import render_template, sendmail
from app.utils.auth_utils import create_access_token

from motor.motor_asyncio import  AsyncIOMotorDatabase
from app.schemas.manager.authSchema import ManagerRegisterRequest, ManagerLoginRequest


@manager_router.post("/register" ,response_class=JSONResponse, tags=["Manager - Registration & Authentication"])
async def manager_register(input_data: ManagerRegisterRequest , db :AsyncIOMotorDatabase = Depends(get_db)):

    name = input_data.name
    id = input_data.id.lower()
    password = input_data.password

    if not name or not id or not password:
        return JSONResponse({"message": "Name, ID, and password are required"}, status_code=400)

    existing_user = await db.personnel.find_one({"id": id})

    if existing_user:
        return JSONResponse({"message": "User already exists"}, status_code=409)
    
    hashed_password = get_hash(password)
    confirm_key = str(uuid.uuid4()).split("-")[0].upper()

    confirmation_link = f"{settings.BASE_URL}/Manager/confirm/{confirm_key}"
    sendmail(
        mail_met={"type": "welcome"},
        receiver=f"{id}@psgtech.ac.in",
        subject="[PSG-GMS-SIGMA] Welcome!",
        short_subject="Welcome!",
        text=f"""Dear {name},
        <br/>Welcome to "SIGMA" General Maintenance Software by PSG College of Technology! Please click the link below to confirm your e-mail and start using the software.
        <br/><br/>
        <a style="text-decoration:none;background-color: #2A4BAA;font-size: 20px;border: none;color: white;border-radius: 10px;padding-top: 10px;padding-bottom: 10px;padding-left: 30px;padding-right: 30px;" href="{confirmation_link}">Confirm E-Mail</a>
        <br/><br/>
        If the button does not work, please visit {confirmation_link} and confirm.
        <br/>Thank You.""",
    )

    await db.personnel.insert_one(
        {
            "name": name,
            "id": id,
            "hashword": hashed_password,
            "confirmed": False,
            "approved": False,
            "mod": 0,
            "confkey": confirm_key,
        }
    )

    return JSONResponse(
        {"message": "Please check your e-mail to confirm your Manager - registration."},
        status_code=201,
    )

@manager_router.get("/confirm/{confkey}", response_class=HTMLResponse, tags=["Manager - Registration & Authentication"])
async def manager_confirm_email(confkey: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await db.personnel.find_one({"confkey": confkey})

    if not user:
        return render_template(
                      "response.html",
                      message="Invalid confirmation key"
        )

    if user.get("confirmed"):
        return render_template(
                     "response.html",
                     message="E-Mail is already confirmed"
        )
    
    mod_key = str(uuid.uuid4()).split("-")[0].upper()

    await db.personnel.update_one(
        {"confkey": confkey},
            {"$set": {"confirmed": True, "approved": False, "mod": 0, "modkey": mod_key}},
    )

    id = user["id"]
    name = user["name"]
    sendmail(
        mail_met={"type": "welcome"},
        receiver=f"{id}@psgtech.ac.in",
        subject="[PSG-GMS-SIGMA] E-Mail Confirmed. Welcome!",
        short_subject="Your E-Mail has been Confirmed!",
        text=f"""Dear {name},
        <br/>Welcome to "SIGMA" General Maintenance Software by PSG College of Technology! Your E-Mail has been Confirmed. Please await approval from a moderator, so you can start using the application!
        <br/>Thank You.""",
    )

    # Fetch all users with mod=1
    mods = await db.personnel.find({"mod": 1}).to_list(length=None)

    for mod in mods:
        sendmail(
            mail_met={"type": "welcome"},
            receiver=f"{mod['id']}@psgtech.ac.in",
            subject="[PSG-GMS-SIGMA] Approve New Manager - Registration",
            short_subject="Please Approve New Manager - Registration to the System",
            text=f"""Dear {mod["name"]},
            <br/>{name} [{id}@psgtech.ac.in] has registered as a maintenance staff under the "SIGMA" General Maintenance Software by PSG College of Technology. Please, as a moderator, approve the user, so {name} can start using the application!
            <br/><br/>
            <a style="text-decoration:none;background-color: #2A4BAA;font-size: 20px;border: none;color: white;border-radius: 10px;padding-top: 10px;padding-bottom: 10px;padding-left: 30px;padding-right: 30px;" href="{settings.BASE_URL}/manager/approve/{mod_key}">Approve User</a>
            <br/><br
            If the button does not work, please visit {settings.BASE_URL}/manager/approve/{confkey} and confirm.
            <br/><br/>
            If you do <b>NOT</b> know who this is, please <b>do NOT</b> confirm.
            <br/>Thank You.""",
        )

    return JSONResponse(
        {"message": "Welcome to \"SIGMA\" General Maintenance Software by PSG College of Technology! Your E-Mail has been Confirmed. Please await approval from a moderator, so you can start using the application!"},
        status_code=200
    )


@manager_router.get("/approve/{confkey}", response_class=HTMLResponse, tags=["Manager - Registration & Authentication"])
async def manager_approve_email(confkey: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await db.personnel.find_one({"confkey": confkey})

    if not user:
        return render_template(
                        "response.html",
                        message="Invalid confirmation key"
        )

    if user.get("approved"):
        return render_template(
                        "response.html",
                        message="User is already approved"
                            )
    
    mod_key = str(uuid.uuid4()).split("-")[0].upper()

    await db.personnel.update_one(
        {"confkey": confkey},
            {"$set": {"confirmed": True, "approved": True, "mod": 0, "modkey": mod_key }},
    )

    id = user["id"]
    name = user["name"]

    mods = await db.personnel.find({"mod": 1}).to_list(length=None)

    for mod in mods:
        sendmail(
            mail_met={"type": "welcome"},
            receiver=f"{mod['id']}@psgtech.ac.in",
            subject="[PSG-GMS-SIGMA] Approve New Manager - Registration",
            short_subject="Please Approve New Manager - Registration to the System",
            text=f"""Dear {mod["name"]},
            <br/>{name} [{id}@psgtech.ac.in] has been approved as a maintenance staff under the "SIGMA" General Maintenance Software by PSG College of Technology. If you wish for {name} to be a moderator, please escalate user privileges by clicking this button:
            <br/><br/>
            <a style="text-decoration:none;background-color: #2A4BAA;font-size: 20px;border: none;color: white;border-radius: 10px;padding-top: 10px;padding-bottom: 10px;padding-left: 30px;padding-right: 30px;" href="{settings.BASE_URL}/manager/escalate/{mod_key}">Escalate User</a>
            <br/><br/>
            If the button does not work, please visit {settings.BASE_URL}/manager/escalate/{mod_key}.
            <br/><br/>
            If you do <b>NOT</b> know who this is, please <b>do NOT</b> confirm.
            <br/>Thank You.""",
        )

    sendmail(
        mail_met={"type": "welcome"},
        receiver=f"{id}@psgtech.ac.in",
        subject="[PSG-GMS-SIGMA] Log-In Account Approved. Welcome!",
        short_subject="Your Log-In Account has been Approved!",
        text=f"""Dear {name},
        <br/>Welcome to "SIGMA" General Maintenance Software by PSG College of Technology! Your Log-In Account has been Approved. Please download and open the application and Log-In as usual so you can start using the application!
        <br/>Thank You.""",
    )

    return render_template(
        "response.html",
        message="You have approved this user. If you wish to escalate this person's privileges and approve as a moderator, check email for further instructions."
    ), 200


@manager_router.delete("/reject/{user_id}" , response_class=JSONResponse, tags=["Manager - Registration & Authentication"] )
async def reject_user(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = db.personnel.find_one({"id": user_id.lower()})

    if not user:
        return JSONResponse({"message": "User not found"},status_code=400)
    
    db.personnel.delete_one({"id": user_id})

    # Send rejection email
    rejection_message = f"""Dear {user['name']},
    <br/>We regret to inform you that your Manager - registration has been rejected. You can reapply and approach a moderator for further assistance.
    <br/><br/>
    Thank You."""

    sendmail(
        mail_met={"type": "rejection"},
        receiver=f"{user_id}@psgtech.ac.in",
        subject="[PSG-GMS-SIGMA] Manager - Registration Rejected",
        short_subject="Manager - Registration Rejected",
        text=rejection_message,
    )

    return JSONResponse({"message": "User has been rejected and notified via email"},status_code=200)

    





@manager_router.post("/login" , response_class=JSONResponse, tags=["Manager - Registration & Authentication"] )
async def Manager_login(input_data: ManagerLoginRequest , db: AsyncIOMotorDatabase = Depends(get_db)):
    id = input_data.id.lower()
    password = input_data.password
    if not id:
        return JSONResponse({"message": "ID is required"},status_code=400)
    if not password:
        return JSONResponse({"message": "Password is required"},status_code=400)
    
    user = await db.personnel.find_one({"id": id})


    if not user:
        return JSONResponse({"message": "User does not exist"}, status_code=401)


    if not get_hash(password) == user["hashword"]:
        return JSONResponse({"message": "Invalid credentials"}, status_code=401)
    

    if not user["confirmed"]:
        return JSONResponse({"message": "Email not confirmed. Please check your email."},status_code=403)
    
    access_token = create_access_token(data={"id": id, "name": user["name"], "mod": user["mod"]})

    user.pop("hashword", None)
    user.pop("_id", None)

    return JSONResponse({"message": "Login successful", "token": access_token, "user": user}, status_code=200)
