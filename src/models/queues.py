from enum import Enum
from pydantic import BaseModel

class EventTypes(Enum):
    read_email = 'read_email',
    list_emails = 'list_emails'

class QueueEvent(BaseModel):
    event: EventTypes
    data: dict