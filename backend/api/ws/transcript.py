from fastapi import APIRouter, WebSocket
from api.ws.manager import manager

router = APIRouter()

@router.websocket("/ws/transcript")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        manager.disconnect(websocket)
