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
    """Check bot recording status"""
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


# ============ EXTRACT PARTICIPANTS ============
async def extract_participants_from_recall(recording: dict) -> dict:
    """
    Extract participant names and IDs from Recall.ai recording data
    Returns: {0: "Chaarukesh", 1: "Balaji", 2: "John"}
    """
    participants_map = {}
    
    try:
        # Try to get from media_shortcuts
        media_shortcuts = recording.get("media_shortcuts", {}) or {}
        
        # Look for participant_events
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
                    
                    # Map participant ID to name
                    if isinstance(participants_list, list):
                        for idx, participant in enumerate(participants_list):
                            if isinstance(participant, dict):
                                name = (
                                    participant.get("name") 
                                    or participant.get("email", "").split("@")[0]
                                    or participant.get("display_name")
                                    or f"Speaker {idx + 1}"
                                )
                                participants_map[idx] = name
                                print(f"   Participant {idx}: {name}")
                    elif isinstance(participants_list, dict):
                        # Handle if it's a dict
                        for key, participant in participants_list.items():
                            if isinstance(participant, dict):
                                name = (
                                    participant.get("name")
                                    or participant.get("email", "").split("@")[0]
                                    or participant.get("display_name")
                                    or f"Speaker {key}"
                                )
                                try:
                                    participants_map[int(key)] = name
                                except:
                                    participants_map[key] = name
                                print(f"   Participant {key}: {name}")
                else:
                    print(f"⚠️ Failed to fetch participants: {resp.status_code}")
        
        if not participants_map:
            print("⚠️ No participants found in media_shortcuts")
            
    except Exception as e:
        print(f"⚠️ Error extracting participants: {e}")
    
    return participants_map


# ============ GET TRANSCRIPT ============
@router.get("/transcript/{bot_id}")
async def get_transcript(bot_id: str):
    """Get transcript after meeting ends using AssemblyAI with Recall.ai participant names"""
    try:
        print(f"📥 Getting transcript for bot: {bot_id}")
        
        # 1️⃣ Get bot status and data
        status_res = requests.get(
            f"{RECALL_BASE_URL}/api/v1/bot/{bot_id}/",
            headers={"Authorization": f"Token {RECALL_API_KEY}"}
        )

        if not status_res.ok:
            raise HTTPException(status_code=404, detail="Bot not found")

        bot_data = status_res.json()
        print(f"✅ Bot data retrieved")
        
        # 2️⃣ Get recordings
        recordings = bot_data.get("recordings", [])
        if not recordings:
            raise HTTPException(
                status_code=404,
                detail=f"No recordings found. Bot status: {bot_data.get('status')}"
            )
        
        recording = recordings[0]
        audio_url = recording.get("audio_url")

        # Fallback: Try media_shortcuts for audio_mixed
        if not audio_url:
            media_shortcuts = recording.get("media_shortcuts", {}) or {}
            audio_mixed = media_shortcuts.get("audio_mixed")
            if isinstance(audio_mixed, dict):
                audio_data = audio_mixed.get("data", {})
                audio_url = audio_data.get("download_url")

        # Fallback: Try media_shortcuts for video_mixed
        if not audio_url:
            media_shortcuts = recording.get("media_shortcuts", {}) or {}
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

        # 3️⃣ Extract participant names from Recall.ai
        print(f"👥 Extracting participant names...")
        participants_map = await extract_participants_from_recall(recording)
        print(f"✅ Participant mapping: {participants_map}")

        # 4️⃣ Transcribe with AssemblyAI
        print(f"🎧 Transcribing with AssemblyAI...")
        assembly_result = transcribe_meeting_with_assembly(audio_url, participants_map)

        print(f"✅ Transcription complete! {assembly_result.get('segments_count', 0)} segments")

        return {
            "success": True,
            "bot_id": bot_id,
            "language": assembly_result.get("language"),
            "segments_count": assembly_result.get("segments_count"),
            "transcript": assembly_result.get("transcript")
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