import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.websockets import manager
from app.core.security import decode_access_token

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket endpoint that accepts authenticated operator connections
    and streams realtime execution events and queue metrics.
    """
    try:
        # Secure connections with the standard JWT verification
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if not subject:
            raise ValueError("Missing subject field in token")
    except Exception as exc:
        logger.warning(f"WebSocket auth failed: {str(exc)}")
        await websocket.close(code=4001)  # Custom WebSocket close code for Auth failure
        return

    # Add to active connection registry
    await manager.connect(websocket)
    
    try:
        # Keep the socket open and listen for close frames
        while True:
            # We discard incoming messages as the channel is strictly downstream broadcast
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.error(f"WebSocket client error: {str(exc)}")
        manager.disconnect(websocket)
