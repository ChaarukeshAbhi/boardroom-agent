from fastapi import APIRouter, HTTPException
import requests
from utils.config import settings
from services.assembly_service import transcribe_meeting_with_assembly
from services.diarization_service import diarize_audio
router = APIRouter(prefix="/api/recall", tags=["Recall"])

RECALL_API_KEY = settings.RECALL_API_KEY
RECALL_BASE_URL = "https://ap-northeast-1.recall.ai"


# ============ JOIN MEETING ============
@router.post("/join")
async def join_meeting(payload: dict):
    """Send bot to join meeting"""
    meeting_url = payload.get("meeting_url")
    agent_name = payload.get("agent_name", "BoardRoom Agent")

    if not meeting_url:
        raise HTTPException(status_code=400, detail="meeting_url missing")

    recall_payload = {
        "meeting_url": meeting_url,
        "bot_name": agent_name,

        # We are NOT using Recall transcription
        "transcription": None,

        "recording": {
            "audio": True
        },
        "webhook_url": settings.RECALL_WEBHOOK_URL
    }

    try:
        res = requests.post(
            f"{RECALL_BASE_URL}/api/v1/bot/",
            headers={
                "Authorization": f"Token {RECALL_API_KEY}",
                "Content-Type": "application/json"
            },
            json=recall_payload
        )

        if not res.ok:
            print(f"❌ Join error: {res.text}")
            raise HTTPException(status_code=500, detail=f"Recall.ai error: {res.text}")

        bot_data = res.json()
        print(f"✅ Bot created: {bot_data.get('id')}")

        return {
            "success": True,
            "id": bot_data.get("id"),
            "bot_id": bot_data.get("id"),
            "status": "Bot joining meeting...",
            "message": "Bot will start recording once meeting begins"
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")


# ============ GET BOT STATUS ============
@router.get("/status/{bot_id}")
async def get_bot_status(bot_id: str):
    """Check bot recording status"""
    try:
        print(f"📊 Fetching status for bot: {bot_id}")

        res = requests.get(
            f"{RECALL_BASE_URL}/api/v1/bot/{bot_id}/",
            headers={"Authorization": f"Token {RECALL_API_KEY}"}
        )

        if not res.ok:
            raise HTTPException(status_code=404, detail="Bot not found")

        data = res.json()

        status = data.get("status", "unknown")
        is_recording = status in ["recording", "active", "joining"]
        recordings = data.get("recordings", [])
        has_audio = len(recordings) > 0

        return {
            "bot_id": bot_id,
            "status": status,
            "is_recording": is_recording,
            "has_audio": has_audio,
            "recording_count": len(recordings)
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")


# ============ EXTRACT PARTICIPANTS ============
async def extract_participants_from_recall(recording: dict) -> dict:
    """
    Extract participant names
    """
    participants_map = {}

    try:
        media_shortcuts = recording.get("media_shortcuts", {}) or {}
        participant_events = media_shortcuts.get("participant_events") or {}

        if isinstance(participant_events, dict):
            pe_data = participant_events.get("data", {})
            participants_url = pe_data.get("participants_download_url")

            if participants_url:
                print(f"📥 Downloading participants from: {participants_url}")
                resp = requests.get(participants_url, timeout=10)

                if resp.ok:
                    participants_list = resp.json()
                    print(f"✅ Raw participants: {participants_list}")

                    for idx, participant in enumerate(participants_list):
                        name = (
                            participant.get("name")
                            or participant.get("email", "").split("@")[0]
                            or f"Speaker {idx+1}"
                        )
                        participants_map[idx] = name
                        print(f"Participant {idx}: {name}")

    except Exception as e:
        print(f"⚠️ Error extracting participants: {e}")

    return participants_map


# ============ GET TRANSCRIPT ============
@router.get("/transcript/{bot_id}")
async def get_transcript(bot_id: str):
    """
    Get transcript using AssemblyAI
    """
    try:
        print(f"📥 Getting transcript for bot: {bot_id}")

        status_res = requests.get(
            f"{RECALL_BASE_URL}/api/v1/bot/{bot_id}/",
            headers={"Authorization": f"Token {RECALL_API_KEY}"}
        )

        if not status_res.ok:
            raise HTTPException(status_code=404, detail="Bot not found")

        bot_data = status_res.json()
        recordings = bot_data.get("recordings", [])

        if not recordings:
            raise HTTPException(status_code=404, detail="No recordings found")

        recording = recordings[0]

        # ---------------------------------------------------
        # FIXED AUDIO SOURCE SELECTION (IMPORTANT)
        # ---------------------------------------------------
        media_shortcuts = recording.get("media_shortcuts", {}) or {}

        audio_url = None

        # Priority 1 → audio_mixed (best quality)
        audio_mixed = media_shortcuts.get("audio_mixed")
        if isinstance(audio_mixed, dict):
            audio_data = audio_mixed.get("data", {})
            audio_url = audio_data.get("download_url")

        # Priority 2 → fallback direct audio
        if not audio_url:
            audio_url = recording.get("audio_url")

        # Priority 3 → fallback video
        if not audio_url:
            video_mixed = media_shortcuts.get("video_mixed")
            if isinstance(video_mixed, dict):
                video_data = video_mixed.get("data", {})
                audio_url = video_data.get("download_url")

        if not audio_url:
            raise HTTPException(
                status_code=404,
                detail="Recording found but no audio/video URL available"
            )

        print(f"✅ Audio URL: {audio_url}")
        speaker_segments = diarize_audio(audio_url)
        # Extract participants
        participants_map = await extract_participants_from_recall(recording)
        print(f"✅ Participant mapping: {participants_map}")

        # Transcribe using Assembly
        assembly_result = transcribe_meeting_with_assembly(audio_url, participants_map, speaker_segments)

        return {
            "success": True,
            "bot_id": bot_id,
            "language": assembly_result.get("language"),
            "segments_count": assembly_result.get("segments_count"),
            "transcript": assembly_result.get("transcript")
        }

    except Exception as e:
        print(f"❌ Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ STOP BOT ============
@router.post("/stop/{bot_id}")
async def stop_bot(bot_id: str):
    try:
        res = requests.post(
            f"{RECALL_BASE_URL}/api/v1/bot/{bot_id}/stop/",
            headers={"Authorization": f"Token {RECALL_API_KEY}"}
        )

        if not res.ok:
            raise HTTPException(status_code=500, detail=res.text)

        return {"success": True}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))