from typing import Optional

import os
import requests
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
import google.generativeai as genai


router = APIRouter(prefix="/gemini", tags=["gemini"])


def _configure_genai() -> None:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY is not set")
    genai.configure(api_key=api_key)


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


def _fetch_url_text(url: str, timeout_seconds: int = 10) -> str:
    try:
        resp = requests.get(url, timeout=timeout_seconds)
        resp.raise_for_status()
        text = resp.text
        # Truncate overly long pages to keep request small
        return text[:200_000]
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {exc}")


@router.post("/analyze")
async def analyze(
    image: Optional[UploadFile] = File(default=None),
    url: Optional[str] = Form(default=None),
    text: Optional[str] = Form(default=None),
    system_prompt: Optional[str] = Form(default=None),
    model: str = Form(default="gemini-2.5-flash"),
):
    """Accepts an image or webpage URL with optional text and system prompt, then calls Gemini."""
    # Require at least one of image or text. URL is optional and additive.
    if not image and not text:
        raise HTTPException(status_code=400, detail="Provide at least one of image or text")

    _configure_genai()

    contents: list[object] = []

    if system_prompt:
        contents.append(system_prompt)

    if image:
        data, mime = _read_upload_bytes(image)
        contents.append({"mime_type": mime, "data": data})

    if url:
        page_text = _fetch_url_text(url)
        contents.append(f"Webpage URL: {url}\n\nContent:\n{page_text}")

    if text:
        contents.append(text)

    try:
        generative_model = genai.GenerativeModel(model_name=model)
        response = generative_model.generate_content(contents=contents)
        result_text = getattr(response, "text", None)
        if not result_text:
            # Fallback: join candidates if available
            result_text = str(response)
        return {"result": result_text}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gemini request failed: {exc}")


