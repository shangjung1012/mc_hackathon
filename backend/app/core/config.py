from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "mc_hackathon backend"
    version: str = "0.1.0"
    cors_allow_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*"
    ]
    
    # Database settings
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/mc_hackathon"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "mc_hackathon"
    database_user: str = "postgres"
    database_password: str = "postgres"
    
    # JWT settings
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Google API settings (optional)
    google_api_key: str = ""
    google_project_id: str = ""
    google_access_token: str = ""
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"  # json, text
    log_file: str = "logs/app.log"
    log_max_bytes: int = 10485760  # 10MB
    log_backup_count: int = 5
    
    class Config:
        env_file = ".env"
        extra = "allow"  # 允許額外的環境變數


settings = Settings()


