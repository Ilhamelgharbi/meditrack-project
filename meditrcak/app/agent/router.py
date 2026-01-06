# app/routers/assistant.py
# app/routers/assistant.py
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, WebSocket
from starlette.responses import StreamingResponse, FileResponse
from fastapi.responses import PlainTextResponse
from xml.etree.ElementTree import Element, tostring
from app.agent.utils.file_upload import save_uploaded_file
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.auth.services import get_current_user, oauth2_scheme
from app.auth.models import User
from app.database.db import get_db
from langchain_core.messages import HumanMessage
import logging
from app.agent.utils.file_upload import save_uploaded_file
from pathlib import Path
import base64
from app.agent.utils.text_to_speech import tts_gtts, tts_elevenlabs, tts
from app.agent.utils.transcribe_audio import transcribe_with_groq
from pathlib import Path
from app.config.settings import settings
from app.chat import services as chat_service
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from app.auth.models import User
from app.agent.agent_dispatcher import ask_agent
from app.agent.whatsapp.media_tools import process_whatsapp_image, determine_media_context, save_whatsapp_media
from app.whatsapp.template_response_handler import handle_whatsapp_template_response

router = APIRouter(prefix="/assistant", tags=["Assistant"])

logger = logging.getLogger(__name__)

# ----------------------------
# Request/Response Schemas
# ----------------------------
class AssistantQuery(BaseModel):
    text: Optional[str] = None
    audio_path: Optional[str] = None  
    image_path: Optional[str] = None  
    output_audio: bool = False
    tts_provider: str = "gtts"
    tool_choice: str = "main"

class AssistantResponse(BaseModel):
    transcription: Optional[str] = None
    agent_response: str
    audio_path: Optional[str] = None
    auto_play: Optional[bool] = False
    image_encoded: Optional[dict] = None
    tools_used: Optional[list] = None
    intent: Optional[str] = None

class ErrorResponse(BaseModel):
    detail: str
    error_type: Optional[str] = None

class UploadResponse(BaseModel):
    audio_path: Optional[str] = None
    image_path: Optional[str] = None

# ----------------------------
# Upload Files Endpoint
# ----------------------------
@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    audio_file: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
):
    """
    Upload audio and/or image files and return their paths.
    """
    audio_path = None
    image_path = None

    if audio_file:
        try:
            audio_path = str(save_uploaded_file(audio_file, "audio"))
        except Exception as e:
            raise HTTPException(500, f"Audio upload failed: {str(e)}")

    if image_file:
        try:
            image_path = str(save_uploaded_file(image_file, "images"))
        except Exception as e:
            raise HTTPException(500, f"Image upload failed: {str(e)}")

    if not audio_file and not image_file:
        raise HTTPException(400, "Provide at least audio or image file.")

    return UploadResponse(audio_path=audio_path, image_path=image_path)

# ----------------------------
# Multi-modal Query Route
# ----------------------------
@router.post("/query", response_model=AssistantResponse)
async def query_assistant(
    text: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
    image_file: Optional[UploadFile] = File(None),
    output_audio: bool = Form(False),
    tts_provider: str = Form("gtts"),
    tool_choice: str = Form("main"),
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Unified multimodal assistant:
    - Accepts text, audio, and/or image
    - Calls agent tools if tool_choice is provided
    - Returns agent response, transcription, optional audio, and image as base64
    """

    if not text and not audio_file and not image_file:
        raise HTTPException(400, "Provide at least text, audio, or image.")

    final_text = text or ""
    transcription = None
    audio_output_path = None
    auto_play = False
    image_base64 = None

    # ----------------- AUDIO -----------------
    if audio_file:
        try:
            audio_path = save_uploaded_file(audio_file, "audio")
            transcription = transcribe_with_groq(str(audio_path))
            if transcription:
                final_text += " " + transcription
                auto_play = True
                print(transcription)
        except Exception as e:
            raise HTTPException(500, f"Audio processing failed: {str(e)}")

    # ----------------- IMAGE -----------------
    if image_file:
        try:
            image_path = save_uploaded_file(image_file, "images")

            # Encode image for frontend display
            import base64
            with open(str(image_path), "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode("utf-8")

            # Determine if user wants pill identification based on message content
            text_lower = final_text.lower() if final_text else ""
            is_pill_request = any(kw in text_lower for kw in ['pill', 'identify', 'tablet', 'medication', 'drug', 'medicine', 'capsule'])

            # Add appropriate instruction based on context
            if not final_text.strip():
                # No text - let agent decide
                final_text = f"Please analyze this medical image and determine if it's a pill to identify or a medical condition to analyze: {image_path}"
            elif is_pill_request:
                # User mentioned pill-related terms - prioritize pill identification
                final_text += f"\n\nPlease identify this pill from the image: {image_path}"
            else:
                # General medical image analysis
                final_text += f"\n\nPlease analyze this medical image: {image_path}"

        except Exception as e:
            raise HTTPException(500, f"Image processing failed: {str(e)}")

    # ----------------- AGENT -----------------
    try:
        from app.agent.agent_dispatcher import ask_agent
        messages = [HumanMessage(content=final_text)]
        user_context = {
            "user_id": str(current_user.id),
            "token": token,
            "role": current_user.role.value  # Add user role to context
        }

        # Only pass tool_choice if you want agent to use a specific tool
        result = ask_agent(messages=messages, user_context=user_context)
        agent_response = result.get("response", "")
        print("Agent response:", agent_response)
        if not agent_response:
            raise HTTPException(500, "Agent returned empty response")
    except Exception as e:
        raise HTTPException(500, f"Agent processing failed: {str(e)}")

    # ----------------- TTS -----------------
    if output_audio and agent_response:
        try:
            tts_result = tts(agent_response, provider=tts_provider)
            if tts_result.get("success"):
                audio_output_path = tts_result.get("audio_path")
                auto_play = True
        except Exception as e:
            logger.warning(f"TTS generation failed: {str(e)}")

    # ----------------- SAVE TO HISTORY -----------------
    try:
        # Determine input type
        input_type = "text"
        if audio_file and image_file:
            input_type = "multimodal"
        elif audio_file:
            input_type = "voice"
        elif image_file:
            input_type = "image"

        # Save user message
        user_content = transcription or text or "Sent an image"
        chat_service.save_message(
            db=db,
            user_id=current_user.id,
            role="user",
            content=user_content,
            input_type=input_type,
            image_url=f"data:image/jpeg;base64,{image_base64}" if image_base64 else None,
        )

        # Save assistant response
        chat_service.save_message(
            db=db,
            user_id=current_user.id,
            role="assistant",
            content=agent_response,
            tools_used=result.get("tools_used", []),
            intent=result.get("intent", "medical"),
            audio_url=audio_output_path,
        )
    except Exception as e:
        logger.warning(f"Failed to save chat history: {str(e)}")

    # ----------------- RETURN -----------------
    return AssistantResponse(
        transcription=transcription,
        agent_response=agent_response,
        audio_path=audio_output_path,
        auto_play=auto_play,
        image_encoded={"base64": image_base64} if image_base64 else None,
        tools_used=result.get("tools_used", []),
        intent=result.get("intent", "medical"),
    )
#----------------------------
# WhatsApp Integration Endpoint
#----------------------------

def _twiml_message(body: str) -> PlainTextResponse:
    response_el = Element('Response')
    message_el = Element('Message')
    message_el.text = body
    response_el.append(message_el)
    xml_bytes = tostring(response_el, encoding='utf-8')
    return PlainTextResponse(content=xml_bytes, media_type='application/xml')


@router.post("/whatsapp_ask")
async def whatsapp_ask(
    From: str = Form(...),
    Body: str = Form(...),
    db: Session = Depends(get_db)
):
    phone = From.replace("whatsapp:", "").strip()
    user_text = Body.strip() if Body else ""

    # ✅ Get user from DB
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        return _twiml_message("❌ User not found. Please register first.")

    # ✅ Check if this is a response to a medication reminder template
    from app.whatsapp.template_response_handler import TemplateResponseHandler
    handler = TemplateResponseHandler(db)

    if handler.is_reminder_response(user_text):
        # Handle as reminder response
        result = handler.handle_reminder_response(From, user_text)
        if result["success"]:
            action = result.get("action", "processed")
            medication = result.get("medication", "medication")
            response_msg = f"✅ {action.title()} confirmed for {medication}."
            if action == "unknown_response":
                response_msg = "Thanks for your response! How can I help you with your medication management?"
            return _twiml_message(response_msg)
        else:
            # If reminder processing failed, continue to agent
            logger.warning(f"Failed to process reminder response: {result.get('error')}")

    # ✅ Build context for agent
    user_context = {
        "user_id": str(user.id),
        "role": user.role.value
    }

    # ✅ Call agent dispatcher
    messages = [HumanMessage(content=user_text)]
    try:
        result = ask_agent(messages=messages, user_context=user_context)
        agent_response = result.get("response", "")
        if not agent_response:
            agent_response = "I'm here to support you, but couldn't generate a response now."
    except Exception as e:
        agent_response = f"❌ Agent error: {str(e)}"

    # ✅ Return Twilio XML
    return _twiml_message(agent_response)
#----------------------------
# Chat History Endpoints
# ----------------------------
class ChatHistoryMessage(BaseModel):
    id: int
    role: str
    content: str
    input_type: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    tools_used: Optional[str] = None
    intent: Optional[str] = None
    timestamp: Optional[str] = None

class ChatHistoryResponse(BaseModel):
    messages: List[ChatHistoryMessage]
    total_count: int

@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get chat history for the current user."""
    messages = chat_service.get_user_history(db, current_user.id, limit, offset)
    total = chat_service.get_message_count(db, current_user.id)
    
    return ChatHistoryResponse(
        messages=[
            ChatHistoryMessage(
                id=msg.id,
                role=msg.role.value,
                content=msg.content,
                input_type=msg.input_type,
                image_url=msg.image_url,
                audio_url=msg.audio_url,
                tools_used=msg.tools_used,
                intent=msg.intent,
                timestamp=msg.created_at.isoformat() if msg.created_at else None,
            )
            for msg in messages
        ],
        total_count=total,
    )

@router.delete("/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear all chat history for the current user."""
    count = chat_service.clear_user_history(db, current_user.id)
    return {"message": f"Cleared {count} messages", "deleted_count": count}

@router.get("/audio/stream/{filename}")
def stream_audio(filename: str):
    audio_path = Path(settings.UPLOADS_PATH) / "audio" / "temp" / filename

    if not audio_path.exists():
        raise HTTPException(404, "Audio file not found")

    def iterfile():
        with audio_path.open("rb") as f:
            while chunk := f.read(8192):
                yield chunk

    return StreamingResponse(iterfile(), media_type="application/octet-stream")

# @router.get("/files/images/{filename}")
# def get_image(filename: str):
#     image_path = Path("uploads/images") / filename

#     if not image_path.exists():
#         raise HTTPException(404, "Image file not found")

#     return FileResponse(image_path, media_type="image/jpeg")

# @router.get("/files/audio/{filename}")
# def get_audio_file(filename: str):
#     audio_path = Path("uploads/audio") / filename

#     if not audio_path.exists():
#         raise HTTPException(404, "Audio file not found")

#     return FileResponse(audio_path, media_type="audio/mpeg")
# # ----------------------------
# # Audio-based Chat Endpoints
# # ----------------------------
# @router.get("/ask")
# async def chat():
#     """Test endpoint to transcribe a saved audio file"""
#     try:
#         audio_path = "app/agent/test3.mp3"
        
#         if not Path(audio_path).exists():
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Audio file not found: {audio_path}"
#             )
        
#         # Transcribe audio using Groq
#         transcript_text = transcribe_with_groq(audio_path)
#         if not transcript_text:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Transcription returned empty text"
#             )
        
#         user_context = {"user_id": 2}
#         from app.agent.agent import ask_agent
#         messages = [HumanMessage(content=transcript_text)]
#         result = ask_agent(messages=messages, user_context=user_context)
#         response = result.get("response", "")
#         if not response:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Agent returned empty response"
#             )
#         print("response:", response)
#         audio_result = tts(response, provider="gtts")
#         if not audio_result.get("success"):
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="TTS generation failed"
#             )
#         audio_path = audio_result.get("audio_path")
        
#         # Verify audio file exists
#         if not Path(audio_path).exists():
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Generated audio file not found"
#             )
        
#         return {
#             "status": "success",
#             "transcription": transcript_text,
#             "agent_response": response,
#             "audio_path": audio_path
#         }

#     except Exception as e:
#         logger.error(f"Audio transcription error: {str(e)}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to transcribe audio: {str(e)}"
#         )

# @router.post("/ask/stream")
# async def post_audio(file: UploadFile = File(...)):
#     """Stream the TTS audio response directly"""
#     try:
#         audio_path = save_uploaded_file(file, "audios")

        
#         # Transcribe audio using Groq
#         transcript_text = transcribe_with_groq(str(audio_path))
#         if not transcript_text:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Transcription returned empty text"
#             )
        
#         user_context = {"user_id": 3}
#         from app.agent.agent import ask_agent
#         messages = [HumanMessage(content=transcript_text)]
#         result = ask_agent(messages=messages, user_context=user_context)
#         response = result.get("response", "")
#         if not response:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Agent returned empty response"
#             )
#         print("response:", response)
#         audio_result = tts(response, provider="gtts")
#         if not audio_result.get("success"):
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="TTS generation failed"
#             )
#         audio_path = audio_result.get("audio_path")
        
#         # Verify audio file exists
#         if not Path(audio_path).exists():
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Generated audio file not found"
#             )
        
#         # Stream the audio file
#         def iterfile():
#             with open(audio_path, "rb") as f:
#                 while chunk := f.read(8192):  # Read in 8KB chunks
#                     yield chunk
        
#         return StreamingResponse(
#             iterfile(),
#             media_type="audio/mpeg",
#         )
        
#     except Exception as e:
#         logger.error(f"Audio streaming error: {str(e)}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to stream audio: {str(e)}"
#         )

# @router.websocket("/ask/live")
# async def chat_live(websocket: WebSocket):
#     """Live streaming endpoint for real-time text and audio"""
#     await websocket.accept()
#     try:
#         # Receive initial audio path or data
#         data = await websocket.receive_json()
#         audio_path = data.get("audio_path", "app/agent/test3.mp3")
        
#         if not Path(audio_path).exists():
#             await websocket.send_json({"error": f"Audio file not found: {audio_path}"})
#             await websocket.close()
#             return
        
#         # Transcribe audio
#         transcript_text = transcribe_with_groq(audio_path)
#         if not transcript_text:
#             await websocket.send_json({"error": "Transcription failed"})
#             await websocket.close()
#             return
        
#         user_context = {"user_id": 2}
#         messages = [HumanMessage(content=transcript_text)]
#         from app.agent.agent import ask_agent_streaming
        
#         accumulated_text = ""
#         async for chunk in ask_agent_streaming(messages, user_context):
#             if "messages" in chunk:
#                 for msg in chunk["messages"]:
#                     if hasattr(msg, "content") and msg.content:
#                         accumulated_text += msg.content
#                         # Send text chunk
#                         await websocket.send_json({
#                             "type": "text",
#                             "content": msg.content
#                         })
                        
#                         # Generate TTS for sentence chunks
#                         if msg.content.strip().endswith((".", "!", "?")):
#                             audio_result = tts(msg.content, provider="gtts")
#                             if audio_result.get("success"):
#                                 with open(audio_result["audio_path"], "rb") as f:
#                                     audio_data = f.read()
#                                 await websocket.send_bytes(audio_data)
        
#         # Send final full audio
#         if accumulated_text:
#             audio_result = tts(accumulated_text, provider="gtts")
#             if audio_result.get("success"):
#                 with open(audio_result["audio_path"], "rb") as f:
#                     audio_data = f.read()
#                 await websocket.send_bytes(audio_data)
                
#     except Exception as e:
#         logger.error(f"Live streaming error: {str(e)}", exc_info=True)
#         await websocket.send_json({"error": str(e)})
#     finally:
#         await websocket.close()

# ----------------------------
# Health Check
# ----------------------------
@router.get("/health")
async def health_check():
    return {"status": "ok"}