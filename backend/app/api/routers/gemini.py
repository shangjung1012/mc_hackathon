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

        # Prefer parsed structured output if available
        if getattr(resp, "parsed", None) is not None:
            return {"result": resp.parsed}
        # Fallback to raw text JSON string
        return {"result": getattr(resp, "text", str(resp))}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gemini request failed: {exc}")

