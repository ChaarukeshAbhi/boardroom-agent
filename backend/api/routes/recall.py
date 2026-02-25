from fastapi import APIRouter, HTTPException
import requests
import os
import tempfile
from utils.config import settings
from services.whisper_service import transcribe_with_segments

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
        audio_url = recording.get("audio_url")

        # ---- NEW: get participant + speaker timeline info for diarization ----
        media_shortcuts = recording.get("media_shortcuts", {}) or {}
        print(f"🔎 media_shortcuts: {media_shortcuts}")

        participant_events = media_shortcuts.get("participant_events") or {}
        pe_data = participant_events.get("data") if isinstance(participant_events, dict) else {}
        participants_url = pe_data.get("participants_download_url")
        speaker_timeline_url = pe_data.get("speaker_timeline_download_url")

        participants_by_id = {}
        speaker_timeline = []

        try:
            if participants_url:
                resp = requests.get(participants_url)
                if resp.ok:
                    participants = resp.json()
                    # Expect a list of participants with id + name
                    for p in participants:
                        pid = p.get("id")
                        if pid is not None:
                            participants_by_id[pid] = p.get("name") or f"Speaker {pid}"
                else:
                    print(f"⚠️ Failed to fetch participants: {resp.status_code}")

            if speaker_timeline_url:
                resp = requests.get(speaker_timeline_url)
                if resp.ok:
                    speaker_timeline = resp.json()
                else:
                    print(f"⚠️ Failed to fetch speaker timeline: {resp.status_code}")
        except Exception as e:
            # Don't fail transcript if diarization fetch fails
            print(f"⚠️ Error fetching diarization data: {e}")

        def infer_speaker_name(t: float) -> str:
            """
            Roughly map a segment start time to the most recent active speaker
            using Recall's speaker_timeline + participants. Falls back to 'Unknown'.
            """
            if not speaker_timeline or not participants_by_id:
                return "Unknown"

            last_speaker_id = None
            last_time = None

            # Events are typically in time order, but sort to be safe
            for ev in sorted(
                speaker_timeline,
                key=lambda e: e.get("timestamp", {}).get("relative", 0.0)
            ):
                ts = ev.get("timestamp", {})
                rel = ts.get("relative")
                if rel is None or rel > t:
                    break

                data = ev.get("data", ev)  # handle either flat or nested "data"
                participant = data.get("participant", {})
                pid = participant.get("id")
                event_type = data.get("event") or ev.get("event")

                if event_type and "speech_on" in event_type:
                    last_speaker_id = pid
                    last_time = rel
                elif event_type and "speech_off" in event_type and pid == last_speaker_id:
                    last_speaker_id = None

            if last_speaker_id is not None:
                return participants_by_id.get(last_speaker_id, f"Speaker {last_speaker_id}")

            return "Unknown"

        # ---- END diarization info fetch ----

        if not audio_url:
            # Prefer an audio/transcript URL if present
            transcript_info = (
                media_shortcuts.get("transcript") or
                media_shortcuts.get("audio_mixed")
            )

            data = transcript_info.get("data") if isinstance(transcript_info, dict) else {}
            audio_url = data.get("download_url")

            # Fallback: use the mixed video URL (Whisper can transcribe mp4)
            if not audio_url:
                video_mixed = media_shortcuts.get("video_mixed")
                if isinstance(video_mixed, dict):
                    video_data = video_mixed.get("data", {})
                    audio_url = video_data.get("download_url")

        if not audio_url:
            raise HTTPException(
                status_code=404,
                detail="Recording found but no audio/transcript/video download URL in Recall response"
            )

        print(f"✅ Audio URL: {audio_url}")

        # 3️⃣ Download audio
        print(f"📥 Downloading audio...")
        audio_response = requests.get(audio_url)
        if not audio_response.ok:
            raise HTTPException(status_code=500, detail="Failed to download audio")

        # Use a cross-platform temporary directory instead of hardcoded /tmp
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"{bot_id}.wav")
        with open(audio_path, "wb") as f:
            f.write(audio_response.content)

        print(f"✅ Audio saved at {audio_path}")

        # 4️⃣ Transcribe with high-accuracy Whisper (see services/whisper_service + config)
        print(f"🎧 Transcribing with Whisper...")
        result = transcribe_with_segments(audio_path)

        # 5️⃣ Format transcript - group by speaker into longer chunks
        def format_timestamp(seconds: float) -> str:
            """Format seconds as MM:SS or HH:MM:SS."""
            total = int(seconds)
            m, s = divmod(total, 60)
            h, m = divmod(m, 60)
            if h:
                return f"{h:02d}:{m:02d}:{s:02d}"
            return f"{m:02d}:{s:02d}"

        # Group consecutive segments by (inferred) speaker
        grouped_segments = []
        current = None
        speaker_order = {}
        next_speaker_idx = 1

        for seg in result["segments"]:
            start_time = float(seg.get("start", 0.0))
            end_time = float(seg.get("end", start_time))
            text = seg.get("text", "").strip()
            if not text:
                continue

            raw_speaker = infer_speaker_name(start_time)

            # Assign stable Speaker N index per raw speaker label
            key = raw_speaker or "Unknown"
            if key not in speaker_order:
                speaker_order[key] = next_speaker_idx
                next_speaker_idx += 1
            speaker_idx = speaker_order[key]

            if raw_speaker and raw_speaker != "Unknown":
                speaker_label = f"Speaker {speaker_idx} ({raw_speaker})"
            else:
                speaker_label = f"Speaker {speaker_idx}"

            # Merge with previous block if same speaker and close in time
            if (
                current
                and current["speaker"] == speaker_label
                and start_time - current["end"] <= 2.0  # seconds gap threshold
            ):
                current["text"] += (" " if current["text"] else "") + text
                current["end"] = end_time
            else:
                if current:
                    grouped_segments.append(current)
                current = {
                    "speaker": speaker_label,
                    "text": text,
                    "start": start_time,
                    "end": end_time,
                }

        if current:
            grouped_segments.append(current)

        final_transcript = []
        for block in grouped_segments:
            final_transcript.append({
                "speaker": block["speaker"],
                "text": block["text"],
                # Display only the starting timestamp of this speaker block
                "timestamp": format_timestamp(block["start"]),
                "start": block["start"],
                "end": block["end"],
            })

        # 6️⃣ Cleanup
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"✅ Cleaned up temp file")

        print(f"✅ Transcription complete! {len(final_transcript)} segments")

        return {
            "success": True,
            "bot_id": bot_id,
            "language": result.get("language"),
            "segments_count": len(final_transcript),
            "transcript": final_transcript
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