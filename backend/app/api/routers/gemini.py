from typing import Optional
import os, requests
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from google import genai
from google.genai import types
from app.schemas.intents import Intent
from .system_prompt import SYSTEM_PROMPT

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
    model: str = Form(default="gemini-2.5-flash"),
):
    """Accepts an image or webpage URL with optional text, then calls Gemini."""
    # Require at least one of image or text. URL is optional and additive.
    if not image and not text:
        raise HTTPException(status_code=400, detail="Provide at least one of image or text")

    client = _client()

    contents: list[object] = []

    if image:
        data, mime = _read_upload_bytes(image)
        contents.append(types.Part.from_bytes(data=data, mime_type=mime))


    if text:
        contents.append(text)

    # Include action as context if provided (e.g., open/shopping/close)
    if action:
        contents.append(f"[action]={action}")

    try:
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
            response_mime_type="application/json",
            response_schema=Intent,
        )

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
                return {"result": speech}
            except Exception:
                pass
        # Fallback to raw text string
        return {"result": getattr(resp, "text", str(resp))}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gemini request failed: {exc}")

