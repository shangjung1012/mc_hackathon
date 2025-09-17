from typing import Literal, Union
from pydantic import BaseModel, Field


class DescribeIntent(BaseModel):
    intent: Literal["describe"] = Field(description="The user's intent type")
    speech: str = Field(
        description=(
            "A single, fluent sentence suitable for TTS summarizing the scene"
        )
    )

class NavigateIntent(BaseModel):
    intent: Literal["navigate"] = Field(description="The user's intent type")
    speech: str = Field(
        description=(
            "Clear, step-by-step guidance suitable for blind users in one paragraph; no colors or 'see the screen'."
        )
    )

class InfoIntent(BaseModel):
    intent: Literal["info"] = Field(description="The user's intent type")
    speech: str = Field(
        description=(
            "Detailed, non-visual information (material, shape, size, smell, usage, etc.) as a single paragraph."
        )
    )

Intent = Union[DescribeIntent, NavigateIntent, InfoIntent]


