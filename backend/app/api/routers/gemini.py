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
    logger.debug("Gemini analysis request", 
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
            logger.debug("Image processed for analysis", mime_type=mime, data_size=len(data))

        if text:
            contents.append(text)
            logger.debug("Text added for analysis", text_length=len(text))

        # 根據模型類型設置配置
        config_params = {
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "response_schema": SpeechResponse,
        }
        
        # 只有支援 thinking 的模型才添加 thinking_config
        if "2.5" in model or "1.5" in model:
            config_params["thinking_config"] = types.ThinkingConfig(thinking_budget=-1)
        
        config = types.GenerateContentConfig(**config_params)

        logger.debug("Sending request to Gemini API", model=model)
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
                    logger.debug("Gemini analysis completed successfully", 
                               speech_length=len(speech))
                    return {"result": speech}
                else:
                    logger.warning("No speech content found in parsed response")
            except Exception as e:
                logger.warning("Failed to parse Gemini response", error=str(e))
                pass
        # Fallback to raw text string
        result = getattr(resp, "text", str(resp))
        logger.debug("Gemini analysis completed with fallback", result_length=len(result))
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
    logger.debug("Gemini analyze-and-speak request", 
                has_image=image is not None, 
                has_text=text is not None, 
                model=model,
                language_code=language_code,
                voice_name=voice_name)
    
    try:
        # 直接調用 analyze 函數獲取文本結果
        analysis_result = await analyze(image, text, model)
        speech_text = analysis_result["result"]
        
        if not speech_text:
            raise HTTPException(status_code=500, detail="No speech content generated")

        logger.debug("Gemini analysis completed", speech_length=len(speech_text))

        # 使用 TTS 合成語音
        try:
            audio_data = synthesize_speech(
                text=speech_text,
                language_code=language_code,
                voice_name=voice_name
            )
            
            logger.debug("TTS synthesis completed successfully", audio_size=len(audio_data))
            
            # 返回音頻流
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

    except HTTPException:
        # 重新拋出 HTTP 異常
        raise
    except Exception as exc:
        logger.error("Gemini analyze-and-speak failed", error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Request failed: {exc}")

