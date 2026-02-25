from fastapi import APIRouter
from utils.database import supabase

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        supabase.table("meetings").select("id").limit(1).execute()
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "message": "BoardRoom Agent API is running!",
        "database": db_status
    }