import time
import requests
from typing import Dict, Any
from utils.config import settings
from difflib import SequenceMatcher
from services.diarization_service import match_utterance_to_speaker

ASSEMBLYAI_BASE_URL = "https://api.assemblyai.com/v2"


def _headers() -> Dict[str, str]:
    return {
        "authorization": settings.ASSEMBLYAI_API_KEY,
        "content-type": "application/json",
    }


def is_similar(a, b, threshold=0.85):
    return SequenceMatcher(None, a, b).ratio() > threshold


def transcribe_meeting_with_assembly(
    audio_url: str,
    participants_map: dict,
    speaker_segments: dict
) -> Dict[str, Any]:

    if not settings.ASSEMBLYAI_API_KEY:
        raise RuntimeError("ASSEMBLYAI_API_KEY is not configured")

    print("🎤 Starting AssemblyAI transcription...")
    print(f"📊 Participants map: {participants_map}")

    # ---------------------------------------------------
    # 1️⃣ Create transcript job
    # ---------------------------------------------------
    create_res = requests.post(
        f"{ASSEMBLYAI_BASE_URL}/transcript",
        json={
            "audio_url": audio_url,

            # Recommended model for multilingual meetings
            "speech_models": ["universal-2"],

            # Speaker mapping handled using Pyannote
            "speaker_labels": False,

            "punctuate": True,
            "format_text": True,
        },
        headers=_headers(),
    )

    if not create_res.ok:
        raise RuntimeError(f"AssemblyAI create error: {create_res.text}")

    job = create_res.json()
    transcript_id = job.get("id")

    if not transcript_id:
        raise RuntimeError("AssemblyAI did not return transcript id")

    print(f"✅ Transcript job created: {transcript_id}")

    # ---------------------------------------------------
    # 2️⃣ Poll until completed
    # ---------------------------------------------------
    data = None
    poll_count = 0

    while True:
        res = requests.get(
            f"{ASSEMBLYAI_BASE_URL}/transcript/{transcript_id}",
            headers=_headers(),
        )

        if not res.ok:
            raise RuntimeError(f"AssemblyAI polling error: {res.text}")

        data = res.json()
        status = data.get("status")

        if status == "completed":
            print("✅ Transcription completed!")
            break

        if status == "error":
            raise RuntimeError(f"AssemblyAI failed: {data.get('error')}")

        poll_count += 1
        print(f"⏳ Processing ({poll_count*3}s): {status}")
        time.sleep(3)

    # ---------------------------------------------------
    # 3️⃣ Use WORD timestamps (IMPORTANT)
    # ---------------------------------------------------
    words = data.get("words", [])

    if not words:
        print("⚠️ No word timestamps returned")
        return {
            "language": data.get("language_code"),
            "segments_count": 0,
            "transcript": []
        }

    print(f"📝 Using words: {len(words)}")

    # ---------------------------------------------------
    # 4️⃣ Merge using diarization timestamps
    # ---------------------------------------------------
    speaker_blocks = []
    current_block = []
    current_speaker = None
    last_text = ""

    BLOCK_TIME_WINDOW = 8   # seconds
    block_start_time = None

    for word in words:

        start = word["start"] / 1000
        end = word["end"] / 1000
        text = (word.get("text") or "").strip()

        if not text:
            continue

        # -----------------------------------------------
        # Remove repetition loops
        # -----------------------------------------------
        if is_similar(text, last_text):
            continue

        last_text = text

        # -----------------------------------------------
        # Match speaker using diarization timestamps
        # -----------------------------------------------
        speaker_id = match_utterance_to_speaker(
            start,
            end,
            speaker_segments
        )

        if current_speaker is None:
            current_speaker = speaker_id
            block_start_time = start

        # -----------------------------------------------
        # Split block when:
        # speaker changes OR time window exceeded
        # -----------------------------------------------
        if (
            speaker_id != current_speaker
            or (start - block_start_time) > BLOCK_TIME_WINDOW
        ):
            if current_block:
                speaker_blocks.append({
                    "speaker": current_speaker,
                    "text": " ".join(current_block)
                })

            current_block = []
            current_speaker = speaker_id
            block_start_time = start

        current_block.append(text)

    if current_block:
        speaker_blocks.append({
            "speaker": current_speaker,
            "text": " ".join(current_block)
        })

    # ---------------------------------------------------
    # 5️⃣ Map speaker IDs → participant names
    # ---------------------------------------------------
    final_transcript = []

    for block in speaker_blocks:
        speaker_id = block["speaker"]

        speaker_name = participants_map.get(
            speaker_id,
            f"Speaker {speaker_id+1}"
        )

        final_transcript.append({
            "speaker": speaker_name,
            "text": block["text"]
        })

    language = data.get("language_code")

    print(f"🌍 Detected language: {language}")
    print(f"✅ Built {len(final_transcript)} transcript blocks")

    return {
        "language": language,
        "segments_count": len(final_transcript),
        "transcript": final_transcript,
    }