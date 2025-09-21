from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import io
import base64
import requests
import os
from app.core.logging import get_logger

logger = get_logger("api.tts")

router = APIRouter(prefix="/tts", tags=["text-to-speech"])

def get_access_token():
    import subprocess
    try:
        result = subprocess.run(['gcloud', 'auth', 'print-access-token'], 
                              capture_output=True, text=True, check=True)
        access_token = result.stdout.strip()
        return access_token
    
    except subprocess.CalledProcessError:
        raise Exception("Failed to get Google Cloud access token, please run 'gcloud auth login' first")

def synthesize_speech(text: str, language_code: str = "cmn-CN", voice_name: str = "cmn-CN-Chirp3-HD-Achernar") -> bytes:
    """
    Synthesize speech using Google Cloud Text-to-Speech API
    
    Args:
        text: Text to convert to speech
        language_code: Language code (default: cmn-CN)
        voice_name: Voice name (default: cmn-CN-Chirp3-HD-Achernar)
    
    Returns:
        Audio data (bytes)
    """
    # Get gcloud project ID and access token
    project_id = os.getenv("GOOGLE_PROJECT_ID")
    access_token = os.getenv("GOOGLE_ACCESS_TOKEN")
    
    # API endpoint
    url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    
    # Request data
    data = {
        "input": {
            "markup": text
        },
        "voice": {
            "languageCode": language_code,
            "name": voice_name,
            "voiceClone": {}
        },
        "audioConfig": {
            "audioEncoding": "LINEAR16"
        }
    }
    
    # Error handling strategy:
    # 1. First attempt: Use existing access token (if available)
    # 2. If first attempt fails: Try gcloud auth print-access-token
    # 3. If second attempt fails: Return error (no fallback to text)
    
    for attempt in range(2):
        try:
            # If this is the second attempt, get fresh access token
            if attempt == 1:
                logger.info("First attempt failed, trying gcloud auth print-access-token...")
                try:
                    access_token = get_access_token()
                    os.environ["GOOGLE_ACCESS_TOKEN"] = access_token
                    logger.info("Successfully obtained new access token from gcloud")
                except Exception as token_error:
                    logger.error(f"Failed to get access token from gcloud: {token_error}")
                    raise Exception(f"Failed to get access token from gcloud: {token_error}")
            
            # Request headers
            headers = {
                "Content-Type": "application/json",
                "X-Goog-User-Project": project_id,
                "Authorization": f"Bearer {access_token}"
            }
            
            # Send POST request
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Decode base64 audio data
            audio_content = base64.b64decode(result["audioContent"])
            
            logger.info(f"TTS synthesis successful on attempt {attempt + 1}")
            return audio_content
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"TTS API request failed on attempt {attempt + 1}: {e}")
            if attempt == 0:
                # First attempt failed, will try gcloud auth on next iteration
                continue
            else:
                # Second attempt also failed, raise error
                raise Exception(f"TTS API request failed after 2 attempts: {e}")
        except KeyError as e:
            raise Exception(f"Response format error, missing field: {e}")
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt == 0:
                continue
            else:
                raise e
    
    # This should never be reached due to the logic above
    raise Exception("All retry attempts failed")


def save_audio_to_file(audio_data: bytes, filename: str = "output.wav") -> str:
    """
    Save audio data to file
    
    Args:
        audio_data: Audio data
        filename: Output filename
    
    Returns:
        File path
    """
    with open(filename, "wb") as f:
        f.write(audio_data)
    return filename


class TTSRequest(BaseModel):
    text: str
    language_code: Optional[str] = "cmn-CN"
    voice_name: Optional[str] = "cmn-CN-Chirp3-HD-Achernar"


class TTSResponse(BaseModel):
    success: bool
    message: str
    audio_url: Optional[str] = None


@router.post("/synthesize", response_model=TTSResponse)
async def synthesize_text_to_speech(request: TTSRequest):
    """
    Convert text to speech
    
    Args:
        request: Request containing text, language code and voice name
        
    Returns:
        Response containing success status and audio URL
    """
    logger.debug("TTS synthesis request", 
                text_length=len(request.text), 
                language_code=request.language_code, 
                voice_name=request.voice_name)
    
    try:
        # Use speech synthesis functionality
        audio_data = synthesize_speech(
            text=request.text,
            language_code=request.language_code,
            voice_name=request.voice_name
        )
        
        # Encode audio data as base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        logger.debug("TTS synthesis completed successfully", audio_size=len(audio_data))
        
        return TTSResponse(
            success=True,
            message="Speech synthesis successful",
            audio_url=f"data:audio/wav;base64,{audio_base64}"
        )
        
    except Exception as e:
        logger.error("TTS synthesis failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Speech synthesis failed: {str(e)}"
        )


@router.post("/synthesize-stream")
async def synthesize_text_to_speech_stream(request: TTSRequest):
    """
    Convert text to speech and return audio data as stream
    
    Args:
        request: Request containing text, language code and voice name
        
    Returns:
        Audio stream data
    """
    logger.debug("TTS stream synthesis request", 
                text_length=len(request.text), 
                language_code=request.language_code, 
                voice_name=request.voice_name)
    
    try:
        # Use speech synthesis functionality
        audio_data = synthesize_speech(
            text=request.text,
            language_code=request.language_code,
            voice_name=request.voice_name
        )
        
        # Create audio stream
        audio_stream = io.BytesIO(audio_data)
        
        logger.debug("TTS stream synthesis completed successfully", audio_size=len(audio_data))
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=synthesized_audio.wav"
            }
        )
        
    except Exception as e:
        logger.error("TTS stream synthesis failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Speech synthesis failed: {str(e)}"
        )
