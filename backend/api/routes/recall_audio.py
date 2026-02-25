from fastapi import APIRouter, Request
import tempfile
import os
import asyncio
from services.whisper_service import transcribe_audio
from api.ws.manager import manager

router = APIRouter()

audio_buffer = bytearray()

@router.post("/api/recall/audio")
async def receive_audio(request: Request):
    global audio_buffer

    chunk = await request.body()
    audio_buffer.extend(chunk)

    # ~3 seconds buffer (adjust if needed)
    if len(audio_buffer) > 16000 * 2 * 3:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_buffer)
            audio_path = f.name

        audio_buffer.clear()

        # Whisper transcription
        result = transcribe_audio(audio_path)

        os.unlink(audio_path)

        if result["text"].strip():
            await manager.broadcast({
                "speaker": "Person 1",   # simple for now
                "language": result["language"],
                "text": result["text"]
            })

    return {"status": "ok"}
