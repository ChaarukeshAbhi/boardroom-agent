from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import meetings, health, auth, recall
from api.ws import transcript
from api.routes import recall_audio

app = FastAPI(
    title="BoardRoom Agent API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(meetings.router)
app.include_router(recall.router)   
app.include_router(transcript.router)
app.include_router(recall_audio.router)

@app.get("/")
async def root():
    return {"message": "BoardRoom Agent API"}