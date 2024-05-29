import uuid
from typing import List
from pydantic import BaseModel, Field


class Email(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    emailId: str = Field(default=None)
    emailFrom: str = Field(default=None)
    emailTo: str = Field(default=None)
    subject: str = Field(default=None)
    tags: str = Field(default=None)
    links: List[str] = Field(default=None)
    status: str = Field(default="PENDING")
