import time
import requests
from typing import Dict, Any
from services.diarization_service import diarize_audio, match_utterance_to_speaker
from utils.config import settings


ASSEMBLYAI_BASE_URL = "https://api.assemblyai.com/v2"


def _headers() -> Dict[str, str]:
    return {
        "authorization": settings.ASSEMBLYAI_API_KEY,
        "content-type": "application/json",
    }


def _format_timestamp(seconds: float) -> str:
    total = int(seconds)
    m, s = divmod(total, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def transcribe_meeting_with_assembly(audio_url: str, participants_map: dict = None) -> Dict[str, Any]:
    """
    AssemblyAI transcription + Pyannote diarization
    """
    if not settings.ASSEMBLYAI_API_KEY:
        raise RuntimeError("ASSEMBLYAI_API_KEY is not configured")

    print(f"🎤 Starting transcription...")

    # 1️⃣ Create transcript job (WITHOUT speaker_labels since we'll use Pyannote)
    create_res = requests.post(
        f"{ASSEMBLYAI_BASE_URL}/transcript",
        json={
            "audio_url": audio_url,
            "speech_models": ["universal-2"],
            "speaker_labels": False,  # ✅ Disable AssemblyAI diarization
            "language_detection": True,
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
        raise RuntimeError("AssemblyAI did not return a transcript id")

    print(f"✅ Transcript job created: {transcript_id}")

    # 2️⃣ Poll until completed
    poll_count = 0
    data = None
    
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
            print(f"✅ Transcription completed!")
            break
        if status == "error":
            raise RuntimeError(f"AssemblyAI failed: {data.get('error')}")

        poll_count += 1
        print(f"⏳ Processing ({poll_count*3}s): {status}")
        time.sleep(3)

    # 3️⃣ Get speaker diarization using Pyannote
    print("🎧 Running speaker diarization...")
    speaker_segments = diarize_audio(audio_url)

    # 4️⃣ Build transcript with correct speakers
    utterances = data.get("utterances") or []
    print(f"📝 Processing {len(utterances)} utterances...")

    language = data.get("language_code")
    if not language:
        lang_det = data.get("language_detection") or []
        if isinstance(lang_det, list) and lang_det:
            language = lang_det[0].get("language")

    print(f"🌍 Language: {language}")

    final_transcript = []
    speaker_seen = set()
    last_speaker = None
    current_block = None

    for utt in utterances:
        text = (utt.get("text") or "").strip()
        if not text:
            continue

        # Get timing
        start_time = utt.get("start", 0) / 1000.0  # Convert ms to seconds
        end_time = utt.get("end", start_time) / 1000.0

        # Match to speaker using Pyannote diarization
        speaker_id = match_utterance_to_speaker(start_time, end_time, speaker_segments)
        
        # Get speaker name
        if participants_map and speaker_id in participants_map:
            speaker_name = participants_map[speaker_id]
        else:
            speaker_name = f"Speaker {chr(65 + speaker_id)}"

        # Group consecutive same-speaker utterances
        if speaker_name == last_speaker and current_block:
            current_block["text"] += " " + text
        else:
            if current_block:
                final_transcript.append(current_block)
            
            current_block = {
                "speaker": speaker_name,
                "text": text,
            }
            last_speaker = speaker_name
            
            if speaker_name not in speaker_seen:
                print(f"🗣️ Speaker: {speaker_name}")
                speaker_seen.add(speaker_name)

    if current_block:
        final_transcript.append(current_block)

    print(f"✅ Built transcript with {len(speaker_seen)} speakers")

    return {
        "language": language,
        "segments_count": len(final_transcript),
        "transcript": final_transcript,
    }