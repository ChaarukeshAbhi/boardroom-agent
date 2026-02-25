import google.generativeai as genai
from utils.config import settings
from utils.database import supabase
from typing import Dict, Any

class ArchivistAgent:
    """
    Archivist Agent: Generates summaries using Google Gemini
    """
    
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        print("✅ Gemini AI configured!")
    
    def generate_summary(self, transcript: str, language: str) -> str:
        """
        Generate meeting summary using Gemini
        
        Args:
            transcript: Full meeting transcript
            language: Detected language
            
        Returns:
            Summary text
        """
        print("📝 Generating summary with Gemini AI...")
        
        prompt = f"""You are analyzing a meeting transcript.

Language detected: {language}

Transcript:
{transcript}

Generate a concise, professional summary with these sections:

**Main Topics Discussed:**
- List 2-3 key topics (bullet points)

**Key Decisions Made:**
- List important decisions (if any)

**Action Items:**
- List tasks with owners (if mentioned)

**Overall Sentiment:**
- Rate as: Positive / Neutral / Negative / Mixed

Keep the summary under 300 words and make it actionable for business context."""

        try:
            response = self.model.generate_content(prompt)
            summary = response.text
            print("✅ Summary generated!")
            return summary
            
        except Exception as e:
            print(f"❌ Gemini error: {str(e)}")
            # Fallback summary
            return f"""**Meeting Summary**

**Language:** {language}

**Transcript Preview:**
{transcript[:500]}...

*Note: Full AI summary generation encountered an error. Please review the transcript above.*"""
    
    def store_meeting(self, meeting_data: Dict[str, Any]) -> str:
        """
        Store meeting in Supabase
        
        Args:
            meeting_data: Dictionary with meeting information
            
        Returns:
            Meeting ID
        """
        print("💾 Storing meeting in database...")
        
        try:
            # Insert meeting
            meeting_response = supabase.table("meetings").insert({
                "title": meeting_data["title"],
                "meeting_url": meeting_data.get("meeting_url", ""),
                "status": "completed",
                "duration_minutes": int(meeting_data.get("duration", 0) / 60)
            }).execute()
            
            meeting_id = meeting_response.data[0]["id"]
            
            # Store transcript
            supabase.table("transcripts").insert({
                "meeting_id": meeting_id,
                "full_text": meeting_data["transcript"],
                "language": meeting_data["language"]
            }).execute()
            
            # Store summary
            supabase.table("summaries").insert({
                "meeting_id": meeting_id,
                "summary_type": "general",
                "content": meeting_data["summary"]
            }).execute()
            
            print(f"✅ Meeting stored! ID: {meeting_id}")
            
            return meeting_id
            
        except Exception as e:
            print(f"❌ Database error: {str(e)}")
            raise