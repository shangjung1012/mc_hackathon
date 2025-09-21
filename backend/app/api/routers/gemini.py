from typing import Optional
import os, requests, io
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends, Request
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
from app.schemas.intents import SpeechResponse
from app.core.logging import get_logger
from app.core.auth import get_current_user_optional
from app.models.user import User
from app.core.database import get_db
from app.services.user_service import UserService
from .system_prompt import SYSTEM_PROMPT, get_system_prompt_with_user
from .tts import synthesize_speech

logger = get_logger("api.gemini")

router = APIRouter(prefix="/gemini", tags=["gemini"])


def get_current_user_from_request(request: Request, db) -> Optional[User]:
    """
    從請求中獲取當前使用者，如果沒有認證則返回 None
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        from jose import JWTError, jwt
        from app.core.config import settings
        
        # 解碼 JWT token
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            return None
        
        # 從資料庫獲取用戶信息
        user_service = UserService(db)
        user = user_service.get_user_by_username(username)
        if user is None:
            logger.warning("User not found in database", username=username)
            return None
        
        logger.debug("User authenticated successfully", username=username, user_id=user.id)
        return user
    except Exception as e:
        logger.debug("Failed to get user from request", error=str(e))
        return None


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
    request: Request,
    image: Optional[UploadFile] = File(default=None),
    text: Optional[str] = Form(default=None),
    system_instruction: Optional[str] = Form(default=None),
    model: str = Form(default="gemini-2.5-flash-lite"),
    db = Depends(get_db),
):
    """Accepts an image or webpage URL with optional text, then calls Gemini."""
    # 獲取當前使用者
    current_user = get_current_user_from_request(request, db)
    
    logger.debug("Gemini analysis request", 
                has_image=image is not None, 
                has_text=text is not None, 
                model=model,
                has_user=current_user is not None)
    
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
        # 優先使用呼叫方傳入的 system_instruction，否則使用包含使用者資料的 SYSTEM_PROMPT
        if system_instruction:
            final_system_instruction = system_instruction
        else:
            final_system_instruction = get_system_prompt_with_user(current_user)
        
        config_params = {
            "system_instruction": final_system_instruction,
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
    request: Request,
    image: Optional[UploadFile] = File(default=None),
    text: Optional[str] = Form(default=None),
    system_instruction: Optional[str] = Form(default=None),
    model: str = Form(default="gemini-2.5-flash-lite"),
    language_code: str = Form(default="cmn-CN"),
    voice_name: str = Form(default="cmn-CN-Chirp3-HD-Achernar"),
    db = Depends(get_db),
):
    """
    Analyze image/text with Gemini and return audio response.
    Combines Gemini analysis with TTS synthesis.
    """
    # 獲取當前使用者
    current_user = get_current_user_from_request(request, db)
    
    logger.debug("Gemini analyze-and-speak request", 
                has_image=image is not None, 
                has_text=text is not None, 
                has_system_instruction=system_instruction is not None,
                model=model,
                language_code=language_code,
                voice_name=voice_name,
                has_user=current_user is not None)
    
    try:
        # 直接調用 analyze 函數獲取文本結果，並傳遞 system_instruction 和 current_user
        analysis_result = await analyze(request, image, text, system_instruction, model, db)
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

