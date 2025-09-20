from typing import Optional
import os, requests
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from google import genai
from google.genai import types
from app.schemas.intents import Intent
from app.core.logging import get_logger
from .system_prompt import SYSTEM_PROMPT

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
    action: Optional[str] = Form(default=None),
    model: str = Form(default="gemini-2.5-flash-lite"),
):
    """Accepts an image or webpage URL with optional text, then calls Gemini."""
    logger.info("Gemini analysis request", 
                has_image=image is not None, 
                has_text=text is not None, 
                action=action, 
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

        # Include action as context if provided (e.g., open/shopping/close)
        if action:
            contents.append(f"[action]={action}")

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
            response_mime_type="application/json",
            response_schema=Intent,
        )

        logger.info("Sending request to Gemini API", model=model)
        resp = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        # Prefer parsed structured output, condensed to a single speech string for TTS
        if getattr(resp, "parsed", None) is not None:
            try:
                parsed = resp.parsed
                # Try attribute first (pydantic object), then dict-style
                speech = getattr(parsed, "speech", None)
                if speech is None and isinstance(parsed, dict):
                    speech = parsed.get("speech")
                # As a fallback, derive minimal text from available fields
                if not speech:
                    intent = getattr(parsed, "intent", None)
                    utterance = getattr(parsed, "utterance", None)
                    if intent is None and isinstance(parsed, dict):
                        intent = parsed.get("intent")
                    if utterance is None and isinstance(parsed, dict):
                        utterance = parsed.get("utterance")
                    speech = (f"{intent or ''}: {utterance or ''}").strip(": ")
                
                logger.info("Gemini analysis completed successfully", 
                           speech_length=len(speech) if speech else 0)
                return {"result": speech}
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

