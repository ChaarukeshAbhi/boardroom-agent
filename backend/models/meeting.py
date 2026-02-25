from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MeetingCreate(BaseModel):
    title: str
    
class MeetingResponse(BaseModel):
    id: str
    title: str
    status: str
    created_at: datetime
    transcript: Optional[str] = None
    summary: Optional[str] = None
    duration_minutes: Optional[int] = None
    language: Optional[str] = None

class TranscriptSegment(BaseModel):
    speaker: str
    start: float
    end: float
    text: str

class ProcessingStatus(BaseModel):
    meeting_id: str
    status: str  # "uploading", "transcribing", "summarizing", "completed", "failed"
    progress: int  # 0-100
    message: str