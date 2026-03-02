import torch
from pyannote.audio import Pipeline
import requests
import tempfile
import os
import ffmpeg
from utils.config import settings


def diarize_audio(audio_url: str) -> dict:
    """
    Run speaker diarization using Pyannote.

    Returns:
        {
            speaker_id: [(start_sec, end_sec), ...]
        }
    """

    try:
        print("🎤 Downloading audio for diarization...")

        audio_response = requests.get(audio_url)
        if not audio_response.ok:
            raise RuntimeError("Failed to download audio")

        temp_dir = tempfile.gettempdir()

        # ---------------------------------------------------
        # Save original file (MP4 from Recall)
        # ---------------------------------------------------
        input_path = os.path.join(temp_dir, "input_meeting_audio.mp4")
        with open(input_path, "wb") as f:
            f.write(audio_response.content)

        # ---------------------------------------------------
        # Convert MP4 → WAV (16kHz mono)  ⭐ IMPORTANT
        # ---------------------------------------------------
        wav_path = os.path.join(temp_dir, "converted_meeting_audio.wav")

        print("🔄 Converting audio to 16kHz mono WAV...")
        (
            ffmpeg
            .input(input_path)
            .output(
                wav_path,
                ac=1,        # mono
                ar=16000     # 16kHz
            )
            .overwrite_output()
            .run(quiet=True)
        )

        # ---------------------------------------------------
        # Load Pyannote pipeline
        # ---------------------------------------------------
        print("🎧 Loading Pyannote pipeline...")

        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=settings.HUGGINGFACE_TOKEN
        )

        # Optional GPU acceleration (if available)
        if torch.cuda.is_available():
            pipeline.to(torch.device("cuda"))
            print("⚡ Using GPU for diarization")

        print("🔄 Running diarization...")
        diarization = pipeline(wav_path)

        # ---------------------------------------------------
        # Convert output format
        # ---------------------------------------------------
        speaker_segments = {}

        for turn, _, speaker in diarization.itertracks(yield_label=True):

            # speaker format: "SPEAKER_00"
            speaker_id = int(speaker.split("_")[-1])

            if speaker_id not in speaker_segments:
                speaker_segments[speaker_id] = []

            speaker_segments[speaker_id].append(
                (float(turn.start), float(turn.end))
            )

        print(f"✅ Found {len(speaker_segments)} speakers")

        # ---------------------------------------------------
        # Cleanup temp files
        # ---------------------------------------------------
        if os.path.exists(input_path):
            os.remove(input_path)

        if os.path.exists(wav_path):
            os.remove(wav_path)

        return speaker_segments

    except Exception as e:
        print(f"⚠️ Diarization error: {e}")
        return {}


def match_utterance_to_speaker(
    utterance_start: float,
    utterance_end: float,
    speaker_segments: dict
) -> int:
    """
    Match a transcript segment to a speaker using timestamp overlap.
    """

    best_speaker = None
    best_overlap = 0.0

    for speaker_id, segments in speaker_segments.items():
        for seg_start, seg_end in segments:

            overlap_start = max(utterance_start, seg_start)
            overlap_end = min(utterance_end, seg_end)

            overlap = max(0.0, overlap_end - overlap_start)

            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = speaker_id

    return best_speaker if best_speaker is not None else 0