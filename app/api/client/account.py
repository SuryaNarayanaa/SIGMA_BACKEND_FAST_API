from fastapi import Depends
from fastapi.responses import JSONResponse

from app.api.client import client_router
from app.database.session import get_db
from app.utils.password_utils import get_hash

from motor.motor_asyncio import  AsyncIOMotorDatabase
from app.schemas.client.accountSchema import ClientAccountRequest, ClientDeleteRequest, ClientUpdateRequest


@client_router.put("/update" , response_class= JSONResponse, tags=["Account Management"])
async def client_update_user(input_data: ClientUpdateRequest , db: AsyncIOMotorDatabase = Depends(get_db) ):

    id = input_data.id
    new_data = input_data.new_data

    if not id:
        return JSONResponse({"message": "ID is required"}, status_code=400)
    
    if not new_data:
        return JSONResponse({"message": "Data for updation is required"}, status_code=400)
    
    user = await db.users.find_one({'id':id})
    if not user:
        return JSONResponse({"message": "User not found"}, status_code=404)

    if "password" in new_data:
        new_data["hashword"] = get_hash(new_data.pop("password"))
    if "hashword" in new_data:
        new_data["hashword"] = get_hash(new_data.pop("hashword"))
        # return JSONResponse({"message": "Password can not be updated"}, status_code=400)

    update_result = await db.users.update_one({"id": id}, {"$set": new_data})

    if update_result.modified_count == 0:
        return JSONResponse({"message": "User data is the same or update failed"}, status_code=400)

    return JSONResponse({"message": "User updated successfully"}, status_code=200)
    
@client_router.delete("/delete", tags=["Account Management"])
async def client_delete_user(input_data: ClientDeleteRequest, db:AsyncIOMotorDatabase = Depends(get_db)):

    id = input_data.id
    if not id:
        return JSONResponse({"message": "ID is required"}, status_code=400)
    
    user = await db.users.find_one({'id':id})
    if not user:
        return JSONResponse({"message": "User not found"}, status_code=404)
    
    delete_result = await db.users.delete_one({"id": id})

    if delete_result.deleted_count == 0:
        return JSONResponse({"message": "User not found or deletion failed"}, status_code=404)

    return JSONResponse({"message": "User deleted successfully"}, status_code=200)

@client_router.post("/account", response_class=JSONResponse, tags=["Account Management"])
async def client_account_page(input_data:ClientAccountRequest,  db:AsyncIOMotorDatabase = Depends(get_db)):
    id = input_data
    if not id:
        return JSONResponse({"message": "ID is required"}, status_code=400)
    
    user = await db.users.find_one({'id':id})
    if not user:
        return JSONResponse({"message": "User not found"}, status_code=404)
    
    user.pop("_id", None)  
    user.pop("hashword", None)

    return JSONResponse({"user": user}, status_code=200)
    
