from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from agents.orchestrator import graph
from services.recall_service import RecallService
from utils.file_handler import save_uploaded_file, validate_file_extension
from utils.database import supabase

router = APIRouter(prefix="/api/meetings", tags=["meetings"])

# Initialize services
orchestrator = graph
recall = RecallService()

class MeetingLinkRequest(BaseModel):
    meeting_url: str
    title: str

@router.post("/join")
async def join_meeting(request: MeetingLinkRequest):
    """
    Send bot to join meeting via link
    """
    try:
        # Create bot
        print(f"🤖 Sending bot to: {request.meeting_url}")
        bot_data = recall.create_bot(request.meeting_url, "BoardRoom Agent")
        
        bot_id = bot_data["id"]
        
        # Store meeting in database
        meeting = supabase.table("meetings").insert({
            "title": request.title,
            "meeting_url": request.meeting_url,
            "status": "bot_joining",
            "platform": "zoom" if "zoom" in request.meeting_url else "meet"
        }).execute()
        
        meeting_id = meeting.data[0]["id"]
        
        # Store bot_id for later retrieval
        supabase.table("meetings").update({
            "meeting_url": bot_id  # Store bot_id temporarily
        }).eq("id", meeting_id).execute()
        
        return {
            "success": True,
            "message": "Bot is joining the meeting!",
            "meeting_id": meeting_id,
            "bot_id": bot_id,
            "status": "Bot will start recording once meeting begins"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{meeting_id}")
async def get_meeting_status(meeting_id: str):
    """
    Get status of meeting bot
    """
    try:
        # Get meeting from database
        meeting = supabase.table("meetings").select("*").eq("id", meeting_id).single().execute()
        
        if not meeting.data:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        bot_id = meeting.data["meeting_url"]  # We stored bot_id here
        
        # Get bot status from Recall.ai
        bot_status = recall.get_bot_status(bot_id)
        
        return {
            "meeting_id": meeting_id,
            "status": bot_status.get("status_changes", [])[-1].get("code") if bot_status.get("status_changes") else "unknown",
            "bot_status": bot_status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process/{meeting_id}")
async def process_meeting(meeting_id: str):
    """
    Process meeting after bot finishes recording
    """
    try:
        # Get meeting
        meeting = supabase.table("meetings").select("*").eq("id", meeting_id).single().execute()
        bot_id = meeting.data["meeting_url"]
        
        # Get transcript from Recall.ai
        print(f"📥 Getting transcript from bot {bot_id}")
        transcript_data = recall.get_transcript(bot_id)
        
        # Generate summary with Gemini
        from agents.archivist import ArchivistAgent
        archivist = ArchivistAgent()
        
        summary = archivist.generate_summary(
            transcript_data["full_text"],
            "en"  # Detect language if needed
        )
        
        # Store transcript
        supabase.table("transcripts").insert({
            "meeting_id": meeting_id,
            "full_text": transcript_data["full_text"],
            "language": "en"
        }).execute()
        
        # Store summary
        supabase.table("summaries").insert({
            "meeting_id": meeting_id,
            "content": summary
        }).execute()
        
        # Update meeting status
        supabase.table("meetings").update({
            "status": "completed"
        }).eq("id", meeting_id).execute()
        
        return {
            "success": True,
            "message": "Meeting processed successfully!",
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_meeting(
    file: UploadFile = File(...),
    title: str = Form(...)
):
    """
    Upload audio/video file (alternative to bot)
    """
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: .mp3, .mp4, .wav, .m4a, .webm"
        )
    
    try:
        file_content = await file.read()
        file_path = save_uploaded_file(file_content, file.filename)
        
        result = await orchestrator.process_meeting(file_path, title)
        
        if result["success"]:
            return JSONResponse({
                "success": True,
                "meeting_id": result["meeting_id"],
                "message": "Meeting processed successfully!",
                "language": result["language"]
            })
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_meetings():
    """Get all meetings"""
    try:
        response = supabase.table("meetings")\
            .select("*, transcripts(language), summaries(content)")\
            .order("created_at", desc=True)\
            .execute()
        
        return {"meetings": response.data}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{meeting_id}")
async def get_meeting(meeting_id: str):
    """Get specific meeting"""
    try:
        response = supabase.table("meetings")\
            .select("*, transcripts(*), summaries(*)")\
            .eq("id", meeting_id)\
            .single()\
            .execute()
        
        return response.data
    
    except Exception as e:
        raise HTTPException(status_code=404, detail="Meeting not found")