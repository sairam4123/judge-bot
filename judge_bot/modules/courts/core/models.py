from pydantic import BaseModel
from datetime import datetime

class Case(BaseModel):
    case_id: int
    reason: str
    status: str  # e.g., "open", "closed", "pending"
    type: str  # e.g., "criminal", "civil"
    created_at: datetime
    updated_at: datetime
    verdict: str | None = None
    summary: str | None = ""
    last_summary_index: int = 0
    court_id: int = 0
    og_message_id: int | None = None
    case_close_reason: str | None = None
    case_closed_at: datetime | None = None


class LogEntry(BaseModel):
    message_id: int
    message_reference_id: int | None = None
    speaker: str
    message: str
    timestamp: datetime
    summary: str | None = ""
    author_id: int
    is_judge: bool = False


class CaseParticipant(BaseModel):
    user_id: int
    role: str  # e.g., "accuser", "accused", "judge"

class Evidence(BaseModel):
    evidence_id: int
    case_id: int

    url: str

    uploader_id: int
    description: str | None = ""
    summary: str | None = ""
    
    created_at: datetime
    filename: str

class Court(BaseModel):
    court_id: int
    name: str
    description: str | None = ""
    created_at: datetime
    guild_id: int
    channel_id: int


class AssociatedCase(BaseModel):
    case_id: int
    associated_case_id: int