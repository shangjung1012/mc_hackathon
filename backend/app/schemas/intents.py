from pydantic import BaseModel, Field


class SpeechResponse(BaseModel):
    speech: str = Field(
        description=(
            "A single, fluent response suitable for TTS. "
            "Provide clear, helpful information based on the user's request. "
            "Keep it concise and natural for speech output."
        )
    )


