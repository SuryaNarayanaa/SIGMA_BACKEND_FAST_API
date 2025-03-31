from pydantic import BaseModel


class ResetPasswordRequest(BaseModel):
    id: str
    old_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    id: str

class ForgotPasswordResetRequest(BaseModel):
    reset_key: str
    new_password: str