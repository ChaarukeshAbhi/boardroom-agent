import whisper
from utils.config import settings
from api.ws.manager import manager

class ObserverAgent:
    def __init__(self):
        print("🎧 Loading Whisper model...")
        self.model = whisper.load_model(settings.WHISPER_MODEL)
        print("✅ Whisper loaded")

        self.speaker_map = {}
        self.speaker_count = 0

    def map_speaker(self, raw_speaker):
        if raw_speaker not in self.speaker_map:
            self.speaker_count += 1
            self.speaker_map[raw_speaker] = f"Person {self.speaker_count}"
        return self.speaker_map[raw_speaker]

    async def transcribe_audio(self, audio_path, raw_speaker):
        result = self.model.transcribe(audio_path)

        speaker = self.map_speaker(raw_speaker)

        payload = {
            "speaker": speaker,
            "language": result["language"],
            "text": result["text"]
        }

        # 🔥 Send to frontend
        await manager.broadcast(payload)
