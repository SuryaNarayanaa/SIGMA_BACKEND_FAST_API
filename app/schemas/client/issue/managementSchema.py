from pydantic import BaseModel
from typing import List, Dict, Optional


class ClientIssueReportRequest(BaseModel):
    id: str
    name: str
    issueType: str
    issueCat: str
    issueContent: str
    block: str
    floor: str
    actionItem: str
    comments: List[Dict[str, str]]  # This will be converted to a comment object in the handler
    survey: Optional[Dict[str, str]] = None  # Optional field for survey
    anonymity: Optional[str] = None  # Optional field for handling anonymity checkbox

class ClientAssignIssueRequest(BaseModel):
    issueNo: str
    assignee: str

class ClientIssueStatusRequest(BaseModel):
    user_id: str

class ClientIssueAddCommentRequest(ClientIssueStatusRequest):
    content: str

class ClientIssueCloseRequest(ClientIssueStatusRequest):
    pass

class ClientIssueOpenRequest(ClientIssueStatusRequest):
    pass

class ClientIssueReportQrRequest(BaseModel):
    id: str
    file: str
    

class ClientSimilarIssuesRequest(BaseModel):
        block: str
        floor: str