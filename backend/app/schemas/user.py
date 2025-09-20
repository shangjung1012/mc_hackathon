from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum


class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class VisionLevelEnum(int, Enum):
    LEVEL_0 = 0  # 接近正常視力
    LEVEL_1 = 1  # 輕度視障
    LEVEL_2 = 2  # 中度視障
    LEVEL_3 = 3  # 重度視障
    LEVEL_4 = 4  # 極重度視障
    LEVEL_5 = 5  # 完全失明


class UserBase(BaseModel):
    username: str
    gender: Optional[GenderEnum] = None
    age: Optional[int] = None
    vision_level: Optional[VisionLevelEnum] = None
    chronic_diseases: Optional[List[str]] = None
    others: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: Optional[str] = None
    gender: Optional[GenderEnum] = None
    age: Optional[int] = None
    vision_level: Optional[VisionLevelEnum] = None
    chronic_diseases: Optional[List[str]] = None
    others: Optional[str] = None


class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
