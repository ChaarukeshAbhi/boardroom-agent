import requests
from utils.config import settings
from typing import Dict, Any

class RecallService:
    """
    Service to interact with Recall.ai API for meeting bot
    """
    
    def __init__(self):
        self.api_key = settings.RECALL_API_KEY
        self.base_url = "https://api.recall.ai/api/v1"
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_bot(self, meeting_url: str, bot_name: str = "BoardRoom Agent") -> Dict[str, Any]:
        """
        Create a bot to join meeting
        
        Args:
            meeting_url: Zoom/Meet URL
            bot_name: Name of the bot
            
        Returns:
            Bot information including bot_id
        """
        endpoint = f"{self.base_url}/bot/"
        
        payload = {
            "meeting_url": meeting_url,
            "bot_name": bot_name,
            "transcription_options": {
                "provider": "assembly_ai"  # or "deepgram"
            },
            "real_time_transcription": {
                "destination_url": None  # We'll get transcript after meeting
            }
        }
        
        response = requests.post(endpoint, json=payload, headers=self.headers)
        
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create bot: {response.text}")
    
    def get_bot_status(self, bot_id: str) -> Dict[str, Any]:
        """Get bot status"""
        endpoint = f"{self.base_url}/bot/{bot_id}/"
        response = requests.get(endpoint, headers=self.headers)
        return response.json()
    
    def get_transcript(self, bot_id: str) -> Dict[str, Any]:
        """Get meeting transcript from bot"""
        endpoint = f"{self.base_url}/bot/{bot_id}/"
        response = requests.get(endpoint, headers=self.headers)
        bot_data = response.json()
        
        # Extract transcript from bot data
        transcript_data = {
            "full_text": "",
            "segments": []
        }
        
        if "transcript" in bot_data:
            for segment in bot_data["transcript"]:
                transcript_data["segments"].append({
                    "speaker": segment.get("speaker", "Unknown"),
                    "text": segment.get("words", ""),
                    "start": segment.get("start", 0),
                    "end": segment.get("end", 0)
                })
            
            transcript_data["full_text"] = " ".join([s["text"] for s in transcript_data["segments"]])
        
        return transcript_data
    
    def delete_bot(self, bot_id: str):
        """Delete/remove bot from meeting"""
        endpoint = f"{self.base_url}/bot/{bot_id}/"
        response = requests.delete(endpoint, headers=self.headers)
        return response.status_code == 204