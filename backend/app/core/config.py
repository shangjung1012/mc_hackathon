from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "mc_hackathon backend"
    version: str = "0.1.0"
    cors_allow_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*"
    ]


settings = Settings()


