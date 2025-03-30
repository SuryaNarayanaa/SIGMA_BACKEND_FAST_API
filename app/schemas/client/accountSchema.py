from pydantic import BaseModel
from typing import Dict, Any

class ClientUpdateRequest(BaseModel):
    id: str
    new_data: Dict[str, Any]

class ClientAccountRequest(BaseModel):
    id: str

class ClientDeleteRequest(ClientAccountRequest):
    pass
