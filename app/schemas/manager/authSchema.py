from pydantic import BaseModel

class ManagerRegisterRequest(BaseModel):
    name: str
    id: str
    password: str
    phone_number: str
    club: str
    club_email: str
    department: str


class ManagerLoginRequest(BaseModel):
    id: str
    password: str

