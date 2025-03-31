from typing import List
from fastapi import Query
from pydantic import BaseModel

class DeleteUserRequest(BaseModel):
    id: str

class UserBase(BaseModel):
    name: str
    id: str
    confirmed: bool
    approved: bool
    confkey: str
    modkey: str

class PendingUsersResponse(BaseModel):
    count: int
    users: List[UserBase]

class UserAccountRequest(BaseModel):
    id: str

class DateRangeParams:
    def __init__(
        self, 
        from_date: str = Query(..., description="Start date in DD-MM-YYYY format"),
        to_date: str = Query(..., description="End date in DD-MM-YYYY format")
    ):
        self.from_date = from_date
        self.to_date = to_date