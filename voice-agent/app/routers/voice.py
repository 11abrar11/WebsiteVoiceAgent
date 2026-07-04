from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.lead_service import lead_service
from app.services.conversation_manager import ConversationManager

router = APIRouter()

@router.websocket("/stream")
async def voice_stream(websocket: WebSocket, email: str = None):
    await websocket.accept()
    
    # ── Lead resolution boundary ────────────────────────────────────
    # Email → LeadService → lead_id.  ConversationManager never sees email.
    lead_id = None
    if email:
        try:
            lead, is_new = await lead_service.get_or_create_lead(email)
            lead_id = lead.id
            tag = "new" if is_new else "returning"
            print(f">>> Lead resolved: id={lead_id}, email={email} ({tag})")
        except ValueError as e:
            print(f">>> Invalid email rejected: {e}")
            await websocket.send_json({"type": "error", "message": str(e)})
            await websocket.close(code=1008, reason="Invalid email")
            return
    
    # ── Initialize ConversationManager with lead_id ─────────────────
    manager = ConversationManager(websocket, lead_id)
    await manager.initialize_persistence()
    
    try:
        # Signal the frontend that the backend is ready (no greeting)
        await websocket.send_json({"type": "ready"})
        
        import asyncio
        import json

        while True:
            message = await websocket.receive()
            
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                    if data.get("type") == "interrupt":
                        manager.interrupt()
                        continue
                except json.JSONDecodeError:
                    pass
                
                # If it's not a JSON interrupt or other command, process it as text input
                if manager.current_task:
                    manager.interrupt()
                manager.current_task = asyncio.create_task(manager.process_user_input(message["text"]))
                
            elif "bytes" in message:
                if manager.current_task:
                    manager.interrupt()
                manager.current_task = asyncio.create_task(manager.process_audio_input(message["bytes"]))
            
    except WebSocketDisconnect:
        print("Client disconnected from voice stream")
    except Exception as e:
        print(f"Error in websocket: {e}")
        try:
            await websocket.close()
        except:
            pass
    finally:
        # Always finalize the conversation (summary + mark completed)
        await manager.finalize_conversation()
