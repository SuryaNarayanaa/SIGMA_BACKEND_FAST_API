from fastapi import Depends
from fastapi.responses import JSONResponse

from app.api.manager import manager_router
from app.database.session import get_db
from app.utils.password_utils import get_hash

from motor.motor_asyncio import  AsyncIOMotorDatabase

