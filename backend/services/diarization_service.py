import torch
from pyannote.audio import Pipeline
import requests
import tempfile
import os
from utils.config import settings

def diarize_audio(audio_url: str) -> dict:
    """
    Use Pyannote for speaker diarization
    Returns: {0: [(start, end)], 1: [(start, end)], ...}
    """
    try:
        print("🎤 Downloading audio for diarization...")
        audio_response = requests.get(audio_url)
        
        # Save to temp file
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, "audio_for_diarization.wav")
        with open(audio_path, "wb") as f:
            f.write(audio_response.content)
        
        print("🎧 Loading Pyannote pipeline...")
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.0",
            token= settings.HUGGINGFACE_TOKEN  
        )
        
        print("🔄 Running diarization...")
        diarization = pipeline(audio_path)
        
        # Convert to format: {speaker_id: [(start_sec, end_sec), ...]}
        speaker_segments = {}
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speaker_id = int(speaker.split("_")[1])  # Extract number from "speaker_0"
            
            if speaker_id not in speaker_segments:
                speaker_segments[speaker_id] = []
            
            speaker_segments[speaker_id].append((turn.start, turn.end))
        
        print(f"✅ Found {len(speaker_segments)} speakers")
        
        # Cleanup
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        return speaker_segments
        
    except Exception as e:
        print(f"⚠️ Diarization error: {e}")
        return {}


def match_utterance_to_speaker(utterance_start: float, utterance_end: float, speaker_segments: dict) -> int:
    """
    Match an utterance to a speaker based on time overlap
    """
    best_speaker = None
    best_overlap = 0
    
    for speaker_id, segments in speaker_segments.items():
        for seg_start, seg_end in segments:
            # Calculate overlap
            overlap_start = max(utterance_start, seg_start)
            overlap_end = min(utterance_end, seg_end)
            overlap = max(0, overlap_end - overlap_start)
            
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = speaker_id
    
    return best_speaker if best_speaker is not None else 0