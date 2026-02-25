import whisper
import os

def download_whisper_model():
    """Download Whisper model to cache"""
    
    print("📥 Downloading Whisper model...")
    print("⏳ This may take 2-5 minutes on first run...")
    
    # Downloads to ~/.cache/whisper/ by default
    model = whisper.load_model("base")
    
    print("✅ Whisper 'base' model downloaded successfully!")
    print(f"📍 Model cached at: {os.path.expanduser('~/.cache/whisper/')}")
    print("\n🎉 Ready to transcribe!")
    
    return model

if __name__ == "__main__":
    download_whisper_model()