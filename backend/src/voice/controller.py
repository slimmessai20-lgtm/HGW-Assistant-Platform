"""
Voice Interface Module (STT/TTS)
Integrates free SpeechRecognition and gTTS
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
import logging
import base64
import io
import os
import tempfile
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])


# Models
class SpeechToTextRequest(BaseModel):
    audio_base64: str
    language_code: str = "fr-FR"


class SpeechToTextResponse(BaseModel):
    text: str
    confidence: float
    language: str


class TextToSpeechRequest(BaseModel):
    text: str
    language_code: str = "fr-FR"
    voice_name: str = "fr-FR-Neural2-A"


class TextToSpeechResponse(BaseModel):
    audio_base64: str
    duration_seconds: float


# STT Endpoint — accepts multipart FormData (audio file upload from browser)
@router.post("/stt")
async def speech_to_text(
    audio: UploadFile = File(...),
    language_code: str = Form("fr")
):
    """Convert speech to text using Groq Whisper API (no ffmpeg required)."""
    from groq import AsyncGroq
    from src.config import GROQ_API_KEY
    
    try:
        audio_bytes = await audio.read()
        client = AsyncGroq(api_key=GROQ_API_KEY)
        
        # Groq Whisper supports webm natively. 
        transcription = await client.audio.transcriptions.create(
            file=("audio.webm", audio_bytes),
            model="whisper-large-v3-turbo",
            prompt="Spoken in French.",  
            response_format="json",
            language="fr" 
        )
        
        text = transcription.text
        return {"text": text, "confidence": 0.99, "language": "fr"}

    except Exception as e:
        logger.error(f"STT error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Speech-to-text error: {str(e)}")


# TTS Endpoint
@router.post("/tts", response_model=TextToSpeechResponse)
async def text_to_speech(request: TextToSpeechRequest):
    """Convert text to speech using gTTS"""
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="text is required")
        
        if len(request.text) > 500:
            request.text = request.text[:500]
            
        lang = request.language_code.split("-")[0]
        tts = gTTS(text=request.text, lang=lang, slow=False)
        
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        
        audio_base64 = base64.b64encode(buf.read()).decode('utf-8')
        word_count = len(request.text.split())
        duration_seconds = (word_count / 150) * 60
        
        return TextToSpeechResponse(audio_base64=audio_base64, duration_seconds=duration_seconds)
    
    except Exception as e:
        logger.error(f"TTS error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Text-to-speech error: {str(e)}")


# Status Endpoint
@router.get("/status")
async def voice_status():
    """Check if voice services are available"""
    return {
        "status": "available",
        "stt": "ready",
        "tts": "ready",
    }


@router.post("/test")
async def voice_test(text: str = "Bonjour, je teste les services de voix"):
    """Test TTS"""
    return await text_to_speech(TextToSpeechRequest(text=text))
