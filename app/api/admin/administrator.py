from fastapi import Depends
from fastapi.responses import JSONResponse

from app.api.admin import admin_router
from app.database.session import get_db
from app.utils.password_utils import get_hash

from motor.motor_asyncio import  AsyncIOMotorDatabase
from pydantic import BaseModel
from fastapi import status


class UserCreate(BaseModel):
    name: str
    id: str 
    password: str

@admin_router.post("/new-user")  # adds new personnel member
async def adm_new_user(user_data: UserCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Adds a new personnel member.
    """
    # Hash the password
    hashed_password = get_hash(user_data.password)

    # Create a new user document
    new_user = {
        "name": user_data.name,
        "id": user_data.id,
        "hashword": hashed_password,
        "confirmed": True,
    }

    # Insert the new user into the database
    try:
        await db["users"].insert_one(new_user)
        return JSONResponse(
            content={"message": "New user created successfully"},
            status_code=201,
        )
    except Exception as e:
        return JSONResponse(
            content={"message": f"Error creating user: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@admin_router.get("/all-users", response_model=dict)
async def all_users_table(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Retrieves all users from the database with efficient querying.
    """
# Use projection to fetch only needed fields
    users_cursor = db.users.find(
        {}, 
        projection={"name": 1, "id": 1, "confirmed": 1, "_id": 0}
    )
    
    my_users = []
    userids = set()  # Using set for faster lookups
    
    async for user in users_cursor:
        status = "CONFIRMED" if str(user.get("confirmed", "")).lower() == "true" else "NOT CONFIRMED"
        my_users.append({
            "name": user.get("name"),
            "id": user.get("id"),
            "status": status,
            "role": "USER",
        })
        userids.add(user.get("id"))
    
    # Fetch admin users with projection
    personnel_cursor = db.personnel.find(
        {}, 
        projection={"name": 1, "id": 1, "confirmed": 1, "_id": 0}
    )
    
    async for admin_user in personnel_cursor:
        if admin_user.get("id") not in userids:
            status = "CONFIRMED" if str(admin_user.get("confirmed", "")).lower() == "true" else "NOT CONFIRMED"
            my_users.append({
                "name": admin_user.get("name"),
                "id": admin_user.get("id"),
                "status": status,
                "role": "ADMIN",
            })
    
    return {
        "users": my_users,
        "title": "[PSG COLLEGE OF TECHNOLOGY | MAINTENANCE] ALL USERS",
    }
