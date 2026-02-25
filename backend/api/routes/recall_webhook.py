from fastapi import APIRouter, Request
from agents.observer import ObserverAgent
import tempfile

router = APIRouter()
observer = ObserverAgent()

@router.post("/api/recall/webhook")
async def recall_webhook(req: Request):
    event = await req.json()

    if event["event"] == "audio.chunk":
        audio_bytes = event["audio"]["data"]
        speaker_id = event["speaker"]["id"]

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            audio_path = f.name

        await observer.transcribe_audio(audio_path, speaker_id)

    return {"ok": True}
