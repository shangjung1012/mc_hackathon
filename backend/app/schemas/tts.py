from pydantic import BaseModel
from typing import Optional


class TTSRequest(BaseModel):
    text: str
    language_code: Optional[str] = "cmn-CN"
    voice_name: Optional[str] = "cmn-CN-Chirp3-HD-Achernar"


class TTSResponse(BaseModel):
    success: bool
    message: str
    audio_url: Optional[str] = None


class TTSErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
