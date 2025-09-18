from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import io
import base64
import requests
import os

router = APIRouter(prefix="/tts", tags=["text-to-speech"])


def synthesize_speech(text: str, language_code: str = "cmn-CN", voice_name: str = "cmn-CN-Chirp3-HD-Achernar") -> bytes:
    """
    使用 Google Cloud Text-to-Speech API 合成語音
    
    Args:
        text: 要轉換成語音的文本
        language_code: 語言代碼 (預設: cmn-CN)
        voice_name: 語音名稱 (預設: cmn-CN-Chirp3-HD-Achernar)
    
    Returns:
        音頻數據 (bytes)
    """
    # 獲取 gcloud 專案 ID 和存取權杖
    project_id = os.getenv("GOOGLE_PROJECT_ID")
    access_token = os.getenv("GOOGLE_ACCESS_TOKEN")
    # import subprocess
    # try:
    #     result = subprocess.run(['gcloud', 'auth', 'print-access-token'], 
    #                           capture_output=True, text=True, check=True)
    #     access_token = result.stdout.strip()
    # except subprocess.CalledProcessError:
    #     raise Exception("無法獲取 Google Cloud 存取權杖，請先執行 'gcloud auth login'")
    
    # API 端點
    url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    
    # 請求標頭
    headers = {
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id,
        "Authorization": f"Bearer {access_token}"
    }
    
    print(headers)
    
    # 請求數據
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
    
    try:
        # 發送 POST 請求
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        # 解析回應
        result = response.json()
        
        # 解碼 base64 音頻數據
        audio_content = base64.b64decode(result["audioContent"])
        
        return audio_content
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"API 請求失敗: {e}")
    except KeyError as e:
        raise Exception(f"回應格式錯誤，缺少欄位: {e}")


def save_audio_to_file(audio_data: bytes, filename: str = "output.wav") -> str:
    """
    將音頻數據保存到檔案
    
    Args:
        audio_data: 音頻數據
        filename: 輸出檔案名稱
    
    Returns:
        檔案路徑
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
    將文字轉換為語音
    
    Args:
        request: 包含文字、語言代碼和語音名稱的請求
        
    Returns:
        包含成功狀態和音頻 URL 的回應
    """
    try:
        # 使用 test.py 中的語音合成功能
        audio_data = synthesize_speech(
            text=request.text,
            language_code=request.language_code,
            voice_name=request.voice_name
        )
        
        # 將音頻數據編碼為 base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return TTSResponse(
            success=True,
            message="語音合成成功",
            audio_url=f"data:audio/wav;base64,{audio_base64}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"語音合成失敗: {str(e)}"
        )


@router.post("/synthesize-stream")
async def synthesize_text_to_speech_stream(request: TTSRequest):
    """
    將文字轉換為語音並以流的形式返回音頻數據
    
    Args:
        request: 包含文字、語言代碼和語音名稱的請求
        
    Returns:
        音頻流數據
    """
    try:
        # 使用 test.py 中的語音合成功能
        audio_data = synthesize_speech(
            text=request.text,
            language_code=request.language_code,
            voice_name=request.voice_name
        )
        
        # 創建音頻流
        audio_stream = io.BytesIO(audio_data)
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=synthesized_audio.wav"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"語音合成失敗: {str(e)}"
        )
