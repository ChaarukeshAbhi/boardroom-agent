import whisper
from utils.config import settings

model = whisper.load_model(settings.WHISPER_MODEL)

# Lazy-loaded larger model for full-meeting transcription (better accuracy)
_transcription_model = None


def _get_transcription_model():
    global _transcription_model
    if _transcription_model is None:
        size = getattr(
            settings, "WHISPER_TRANSCRIPTION_MODEL", None
        ) or settings.WHISPER_MODEL
        print(f"🎧 Loading Whisper transcription model: {size}")
        _transcription_model = whisper.load_model(size)
        print("✅ Transcription model loaded!")
    return _transcription_model


def transcribe_audio(audio_path: str):
    result = model.transcribe(
        audio_path,
        language=None,
        fp16=False
    )

    return {
        "text": result.get("text", ""),
        "language": result.get("language", "unknown")
    }


def transcribe_with_segments(audio_path: str):
    """
    High-accuracy transcription for full meeting recordings.
    Uses a larger model plus Whisper's default sampling + safety thresholds
    to reduce repetitions and hallucinations.
    Returns the raw Whisper result (with "segments", "language", etc.).
    """
    m = _get_transcription_model()

    result = m.transcribe(
        audio_path,
        language=None,
        fp16=False,
        # Temperature fallback & thresholds are robust against repetition
        temperature=(0.0, 0.2, 0.4, 0.6, 0.8),
        compression_ratio_threshold=2.4,
        logprob_threshold=-1.0,
        no_speech_threshold=0.6,
    )
    return result
