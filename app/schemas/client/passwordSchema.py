from pydantic import BaseModel

class ClientForgotPasswordRequest(BaseModel):
    id: str
    
class ClientForgotPasswordResetRequest(BaseModel):
    reset_key: str
    new_password: str

class ClientResetPasswordReqeust(BaseModel):
    id: str
    old_password: str
    new_password: str