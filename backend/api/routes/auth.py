from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client

from utils.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

# -------------------- SUPABASE CLIENT --------------------

print("DEBUG SUPABASE_URL =", settings.SUPABASE_URL)
print("DEBUG SUPABASE_KEY =", "FOUND" if settings.SUPABASE_KEY else None)

supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)

# -------------------- MODELS --------------------

class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

# -------------------- ROUTES --------------------

@router.post("/signup")
async def signup(req: SignupRequest):
    try:
        res = supabase.auth.sign_up({
            "email": req.email,
            "password": req.password
        })

        # 🔍 LOG FULL RESPONSE
        print("SUPABASE SIGNUP RESPONSE:", res)

        if res.user is None:
            raise HTTPException(
                status_code=400,
                detail=res.error.message if res.error else "Signup failed"
            )

        return {
            "message": "Signup successful",
            "user_id": res.user.id,
            "email": res.user.email
        }

    except Exception as e:
        print("SIGNUP ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
async def login(req: LoginRequest):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": req.email,
            "password": req.password
        })

        if response.session is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": {
                "id": response.user.id,
                "email": response.user.email
            }
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
