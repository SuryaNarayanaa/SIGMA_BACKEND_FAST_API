import uuid
from fastapi import Depends
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.client import client_router
from app.database.session import get_db

from app.utils.password_utils import get_hash
from app.utils.email_utils import sendmail
from app.utils.auth_utils import create_access_token

from motor.motor_asyncio import  AsyncIOMotorDatabase
from app.schemas.client.authSchema import ClientRegisterRequest, ClientLoginRequest


@client_router.post("/register" ,response_class=JSONResponse, tags=["Registration & Authentication"])
async def client_register(input_data: ClientRegisterRequest , db :AsyncIOMotorDatabase = Depends(get_db)):

    name = input_data.name
    id = input_data.id.lower()
    password = input_data.password
    phone_number = input_data.phone_number
    club = input_data.club
    club_email = input_data.club_email
    department = input_data.department

    if not name or not id or not password:
        return JSONResponse({"message": "Name, ID, and password are required"}, status_code=400)

    existing_user = await db.users.find_one({"id": id})

    if existing_user:
        return JSONResponse({"message": "User already exists"}, status_code=409)
    
    hashed_password = get_hash(password)
    confirm_key = str(uuid.uuid4()).split("-")[0].upper()

    confirmation_link = f"{settings.BASE_URL}/client/confirm/{confirm_key}"
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

    await db.users.insert_one(
        {
            "name": name,
            "id": id,
            "phone_number": phone_number,
            "club": club,
            "club_email": club_email,
            "department": department,
            "hashword": hashed_password,
            "confirmed": False,
            "confkey": confirm_key,
        }
    )

    return JSONResponse(
        {"message": "Please check your e-mail to confirm your registration."},
        status_code=201,
    )

@client_router.get("/confirm/{confirm_key}", response_class=JSONResponse, tags=["Registration & Authentication"])
async def client_confirm_email(confirm_key: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await db.users.find_one({"confkey": confirm_key})

    if not user:
        return JSONResponse(
            {"message": "The confirmation key you provided is invalid. Please check your email or contact support."},
            status_code=400
        )

    # Update user as confirmed
    await db.users.update_one(
        {"confkey": confirm_key}, {"$set": {"confirmed": True, "confkey": ""}}
    )

    return JSONResponse(
        {"message": "Email confirmed successfully! You can now log in to your account."},
        status_code=200
    )

@client_router.post("/login" , response_class=JSONResponse, tags=["Registration & Authentication"] )
async def client_login(input_data: ClientLoginRequest , db: AsyncIOMotorDatabase = Depends(get_db)):
    id = input_data.id.lower()
    password = input_data.password
    if not id:
        return JSONResponse({"message": "ID is required"},status_code=400)
    if not password:
        return JSONResponse({"message": "Password is required"},status_code=400)
    
    user = await db.users.find_one({"id": id})


    if not user:
        return JSONResponse({"message": "User does not exist"}, status_code=401)


    if not get_hash(password) == user["hashword"]:
        return JSONResponse({"message": "Invalid credentials"}, status_code=401)
    

    if not user["confirmed"]:
        return JSONResponse({"message": "Email not confirmed. Please check your email."},status_code=403)
    
    access_token = create_access_token(data={"id": id, "name": user["name"], "phone_number": user["phone_number"]})

    user.pop("hashword", None)
    user.pop("_id", None)

    return JSONResponse({"message": "Login successful", "token": access_token, "user": user}, status_code=200)
