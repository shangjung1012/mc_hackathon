from sqlalchemy import Column, Integer, String, DateTime, Enum, ARRAY
from sqlalchemy.sql import func
from ..core.database import Base
import enum


class GenderEnum(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class VisionLevelEnum(enum.Enum):
    LEVEL_0 = 0  # 接近正常視力
    LEVEL_1 = 1  # 輕度視障
    LEVEL_2 = 2  # 中度視障
    LEVEL_3 = 3  # 重度視障
    LEVEL_4 = 4  # 極重度視障
    LEVEL_5 = 5  # 完全失明


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    gender = Column(Enum(GenderEnum), nullable=True)
    age = Column(Integer, nullable=True)
    vision_level = Column(Enum(VisionLevelEnum), nullable=True)
    chronic_diseases = Column(ARRAY(String), nullable=True)  # 慢性病列表
    others = Column(String, nullable=True)  # 其他資訊
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
