from pydantic import BaseModel

class UserIDBaseModel(BaseModel):
    user_id: str

class TasksIssueCloseRequest(UserIDBaseModel):
    pass

class TasksIssueOpenRequest(UserIDBaseModel):
    pass

class TasksIssueAddCommentRequest(UserIDBaseModel):
    content: str
