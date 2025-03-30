from pydantic import BaseModel

class IssueStatusRequest(BaseModel):
    id: str