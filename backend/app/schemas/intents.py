from typing import Literal, Union
from pydantic import BaseModel, Field


class DescribeIntent(BaseModel):
    intent: Literal["describe"] = Field(description="The user's intent type")
    left: str = Field(description="Description of items on the left; empty if none")
    center: str = Field(description="Description of items in the center; empty if none")
    right: str = Field(description="Description of items on the right; empty if none")
    utterance: str = Field(description="Original transcribed user speech text")


class NavigateIntent(BaseModel):
    intent: Literal["navigate"] = Field(description="The user's intent type")
    target: str = Field(description="Object or area the user wants to reach")
    direction: str = Field(
        description=(
            "Clear, non-visual guidance suitable for blind users. No colors or 'see the screen'."
        )
    )
    arrived: bool = Field(description="Whether the user has arrived at the target")
    utterance: str = Field(description="Original transcribed user speech text")


class InfoIntent(BaseModel):
    intent: Literal["info"] = Field(description="The user's intent type")
    target: str = Field(description="Object the user wants information about")
    info: str = Field(
        description=(
            "Detailed, non-visual information (brand, price, size, material, usage, etc.)."
        )
    )
    utterance: str = Field(description="Original transcribed user speech text")


Intent = Union[DescribeIntent, NavigateIntent, InfoIntent]


