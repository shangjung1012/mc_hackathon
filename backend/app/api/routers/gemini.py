from typing import Optional
import os, requests, io
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
from app.schemas.intents import SpeechResponse
from app.core.logging import get_logger
from .system_prompt import SYSTEM_PROMPT
from .tts import synthesize_speech

logger = get_logger("api.gemini")

router = APIRouter(prefix="/gemini", tags=["gemini"])


def _client() -> genai.Client:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY is not set")
    return genai.Client(api_key=api_key)


def _read_upload_bytes(upload: UploadFile) -> tuple[bytes, str]:
    try:
        data = upload.file.read()
    finally:
        try:
            upload.file.close()
        except Exception:
            pass
    mime = upload.content_type or "application/octet-stream"
    return data, mime


@router.post("/analyze")
async def analyze(
    image: Optional[UploadFile] = File(default=None),
    text: Optional[str] = Form(default=None),
    model: str = Form(default="gemini-2.5-flash-lite"),
):
    """Accepts an image or webpage URL with optional text, then calls Gemini."""
    logger.info("Gemini analysis request", 
                has_image=image is not None, 
                has_text=text is not None, 
                model=model)
    
    # Require at least one of image or text. URL is optional and additive.
    if not image and not text:
        logger.warning("Gemini analysis failed: no input provided")
        raise HTTPException(status_code=400, detail="Provide at least one of image or text")

    try:
        client = _client()

        contents: list[object] = []

        if image:
            data, mime = _read_upload_bytes(image)
            contents.append(types.Part.from_bytes(data=data, mime_type=mime))
            logger.info("Image processed for analysis", mime_type=mime, data_size=len(data))

        if text:
            contents.append(text)
            logger.info("Text added for analysis", text_length=len(text))


        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
            response_mime_type="application/json",
            response_schema=SpeechResponse,
        )

        logger.info("Sending request to Gemini API", model=model)
        resp = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        # Parse structured output to get speech response
        if getattr(resp, "parsed", None) is not None:
            try:
                parsed = resp.parsed
                # Get speech attribute from parsed response
                speech = getattr(parsed, "speech", None)
                if speech is None and isinstance(parsed, dict):
                    speech = parsed.get("speech")
                
                if speech:
                    logger.info("Gemini analysis completed successfully", 
                               speech_length=len(speech))
                    return {"result": speech}
                else:
                    logger.warning("No speech content found in parsed response")
            except Exception as e:
                logger.warning("Failed to parse Gemini response", error=str(e))
                pass
        # Fallback to raw text string
        result = getattr(resp, "text", str(resp))
        logger.info("Gemini analysis completed with fallback", result_length=len(result))
        return {"result": result}
    except Exception as exc:
        logger.error("Gemini analysis failed", error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gemini request failed: {exc}")


@router.post("/analyze-and-speak")
async def analyze_and_speak(
    image: Optional[UploadFile] = File(default=None),
    text: Optional[str] = Form(default=None),
    model: str = Form(default="gemini-2.5-flash-lite"),
    language_code: str = Form(default="cmn-CN"),
    voice_name: str = Form(default="cmn-CN-Chirp3-HD-Achernar"),
):
    """
    Analyze image/text with Gemini and return audio response.
    Combines Gemini analysis with TTS synthesis.
    """
    logger.info("Gemini analyze-and-speak request", 
                has_image=image is not None, 
                has_text=text is not None, 
                model=model,
                language_code=language_code,
                voice_name=voice_name)
    
    # Require at least one of image or text
    if not image and not text:
        logger.warning("Gemini analyze-and-speak failed: no input provided")
        raise HTTPException(status_code=400, detail="Provide at least one of image or text")

    try:
        # First, get text analysis from Gemini
        client = _client()

        contents: list[object] = []

        if image:
            data, mime = _read_upload_bytes(image)
            contents.append(types.Part.from_bytes(data=data, mime_type=mime))
            logger.info("Image processed for analysis", mime_type=mime, data_size=len(data))

        if text:
            contents.append(text)
            logger.info("Text added for analysis", text_length=len(text))

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
            response_mime_type="application/json",
            response_schema=SpeechResponse,
        )

        logger.info("Sending request to Gemini API", model=model)
        resp = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        # Extract speech text from Gemini response
        speech_text = None
        if getattr(resp, "parsed", None) is not None:
            try:
                parsed = resp.parsed
                speech_text = getattr(parsed, "speech", None)
                if speech_text is None and isinstance(parsed, dict):
                    speech_text = parsed.get("speech")
            except Exception as e:
                logger.warning("Failed to parse Gemini response", error=str(e))
        
        # Fallback to raw text if parsing failed
        if not speech_text:
            speech_text = getattr(resp, "text", str(resp))
        
        if not speech_text:
            raise HTTPException(status_code=500, detail="No speech content generated")

        logger.info("Gemini analysis completed", speech_length=len(speech_text))

        # Now synthesize speech using TTS
        try:
            audio_data = synthesize_speech(
                text=speech_text,
                language_code=language_code,
                voice_name=voice_name
            )
            
            logger.info("TTS synthesis completed successfully", audio_size=len(audio_data))
            
            # Return audio as streaming response
            return StreamingResponse(
                io.BytesIO(audio_data),
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "attachment; filename=response.wav"
                }
            )
            
        except Exception as tts_error:
            logger.error("TTS synthesis failed", error=str(tts_error), exc_info=True)
            raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {tts_error}")

    except Exception as exc:
        logger.error("Gemini analyze-and-speak failed", error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Request failed: {exc}")

