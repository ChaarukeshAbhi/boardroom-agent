from fastapi import APIRouter, HTTPException
import requests
from utils.config import settings
from services.assembly_service import transcribe_meeting_with_assembly

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
        "transcription": {
            "provider": "recall",
            "language": "auto"
        },
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
    """Check bot recording status - FIXED"""
    try:
        print(f"📊 Fetching status for bot: {bot_id}")
        
        res = requests.get(
            f"{RECALL_BASE_URL}/api/v1/bot/{bot_id}/",
            headers={"Authorization": f"Token {RECALL_API_KEY}"}
        )

        if not res.ok:
            print(f"❌ Status error: {res.status_code} - {res.text}")
            raise HTTPException(status_code=404, detail="Bot not found")

        data = res.json()
        print(f"✅ Raw response: {data}")
        
        # Parse status correctly
        status = data.get("status", "unknown")
        is_recording = status in ["recording", "active", "joining"]
        recordings = data.get("recordings", [])
        has_audio = len(recordings) > 0
        
        print(f"📊 Parsed - Status: {status}, Recording: {is_recording}, Has Audio: {has_audio}")
        
        return {
            "bot_id": bot_id,
            "status": status,
            "is_recording": is_recording,
            "has_audio": has_audio,
            "recording_count": len(recordings)
        }

    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")


# ============ GET TRANSCRIPT ============
@router.get("/transcript/{bot_id}")
async def get_transcript(bot_id: str):
    """Get transcript after meeting ends"""
    try:
        print(f"📥 Getting transcript for bot: {bot_id}")
        
        # 1️⃣ Get bot status
        status_res = requests.get(
            f"{RECALL_BASE_URL}/api/v1/bot/{bot_id}/",
            headers={"Authorization": f"Token {RECALL_API_KEY}"}
        )

        if not status_res.ok:
            raise HTTPException(status_code=404, detail="Bot not found")

        bot_data = status_res.json()
        print(f"✅ Bot data retrieved")
        print(f"📄 Raw bot data: {bot_data}")
        
        # 2️⃣ Get recordings
        recordings = bot_data.get("recordings", [])
        print(f"🎧 Recordings list: {recordings}")
        if not recordings:
            raise HTTPException(
                status_code=404,
                detail=f"No recordings found in Recall response. Bot status: {bot_data.get('status')}"
            )
        
        recording = recordings[0]

        # Prefer direct audio_url if Recall provides it
        audio_url = recording.get("audio_url")

        # Fallbacks via media_shortcuts if needed
        media_shortcuts = recording.get("media_shortcuts", {}) or {}
        if not audio_url:
            transcript_info = (
                media_shortcuts.get("audio_mixed")
                or media_shortcuts.get("transcript")
            )
            data = transcript_info.get("data") if isinstance(transcript_info, dict) else {}
            audio_url = data.get("download_url")

        if not audio_url:
            video_mixed = media_shortcuts.get("video_mixed")
            if isinstance(video_mixed, dict):
                video_data = video_mixed.get("data", {})
                audio_url = video_data.get("download_url")

        if not audio_url:
            raise HTTPException(
                status_code=404,
                detail="Recording found but no downloadable audio/video URL for transcription"
            )

        print(f"✅ Using audio URL for AssemblyAI: {audio_url}")

        # 3️⃣ Transcribe via AssemblyAI (handles speakers + text)
        try:
            assembly_result = transcribe_meeting_with_assembly(audio_url)
        except Exception as e:
            print(f"❌ AssemblyAI error: {e}")
            raise HTTPException(status_code=500, detail=f"AssemblyAI error: {e}")

        print(f"✅ AssemblyAI transcription complete! {assembly_result.get('segments_count', 0)} segments")

        return {
            "success": True,
            "bot_id": bot_id,
            **assembly_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============ STOP BOT ============
@router.post("/stop/{bot_id}")
async def stop_bot(bot_id: str):
    """Stop bot recording"""
    try:
        res = requests.post(
            f"{RECALL_BASE_URL}/api/v1/bot/{bot_id}/stop/",
            headers={"Authorization": f"Token {RECALL_API_KEY}"}
        )

        if not res.ok:
            raise HTTPException(status_code=500, detail=f"Failed to stop bot: {res.text}")

        return {
            "success": True,
            "message": "Bot stopped successfully",
            "bot_id": bot_id
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")


# ============ GET ALL BOTS ============
@router.get("/bots/")
async def list_bots():
    """List all bots"""
    try:
        res = requests.get(
            f"{RECALL_BASE_URL}/api/v1/bot/",
            headers={"Authorization": f"Token {RECALL_API_KEY}"}
        )

        if not res.ok:
            raise HTTPException(status_code=500, detail="Failed to fetch bots")

        bots = res.json()
        return {
            "success": True,
            "total_bots": len(bots),
            "bots": bots
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")