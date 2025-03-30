from pydantic import BaseModel

class ClientRegisterRequest(BaseModel):
    name: str
    id: str
    password: str
    phone_number: str
    club: str
    club_email: str
    department: str


class ClientLoginRequest(BaseModel):
    id: str
    password: str

