from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from utils.config import settings
from utils.database import supabase

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

class ChatRequest(BaseModel):
    message: str
    meeting_id: str = None  # Optional: Chat about specific meeting

@router.post("/")
async def chat(request: ChatRequest):
    """
    AI Chatbot to answer questions about meetings
    """
    try:
        context = ""
        
        # If meeting_id provided, get meeting context
        if request.meeting_id:
            meeting = supabase.table("meetings")\
                .select("*, transcripts(*), summaries(*)")\
                .eq("id", request.meeting_id)\
                .single()\
                .execute()
            
            if meeting.data:
                transcript = meeting.data.get("transcripts", [{}])[0].get("full_text", "")
                summary = meeting.data.get("summaries", [{}])[0].get("content", "")
                
                context = f"""
Meeting: {meeting.data['title']}

Summary:
{summary}

Full Transcript:
{transcript[:2000]}...  
"""
        else:
            # Get all meetings for general questions
            meetings = supabase.table("meetings")\
                .select("title, summaries(content)")\
                .limit(5)\
                .order("created_at", desc=True)\
                .execute()
            
            context = "Recent meetings:\n"
            for m in meetings.data:
                summary = m.get("summaries", [{}])[0].get("content", "No summary")
                context += f"\n{m['title']}: {summary[:200]}...\n"
        
        # Generate response with Gemini
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""You are a helpful AI assistant for BoardRoom Agent, a meeting intelligence system.

Context about meetings:
{context}

User question: {request.message}

Provide a helpful, concise answer based on the meeting data. If the question cannot be answered from the available meetings, say so politely."""

        response = model.generate_content(prompt)
        
        return {
            "success": True,
            "response": response.text,
            "meeting_context": request.meeting_id is not None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))