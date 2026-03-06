from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from agents.archivist import ArchivistAgent

router = APIRouter(prefix="/api/archive", tags=["archive"])

archivist = ArchivistAgent()


class TranscriptSegment(BaseModel):
    speaker: str
    text: str
    timestamp: str
    confidence: float | None = None
    language: str | None = None


class TranscriptRequest(BaseModel):
    bot_id: str
    transcript: List[TranscriptSegment]


@router.post("/store")
def store_transcript(data: TranscriptRequest):

    archivist.store_transcript(
        meeting_id=data.bot_id,
        transcript=[segment.dict() for segment in data.transcript]
    )

    return {"status": "saved"}