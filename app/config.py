"""
Application Configuration
Loads settings from environment variables
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Q-Docs"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Database
    DATABASE_URL: str = "sqlite:///./dms.db"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://74.225.253.72:3002", "http://74.225.253.72:6002", "https://ambitious-moss-06e3a3810.7.azurestaticapps.net"]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # Initial Admin User
    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_EMAIL: str = "admin@pharma-dms.com"
    FIRST_ADMIN_PASSWORD: str = "Admin@123456"
    
    # Password Policy
    MIN_PASSWORD_LENGTH: int = 8
    REQUIRE_PASSWORD_CHANGE_ON_RESET: bool = True
    
    # Audit
    AUDIT_LOG_RETENTION_DAYS: int = 2555  # ~7 years for pharma compliance
    
    # Email/SMTP Configuration
    SMTP_HOST: Optional[str] = "smtp.gmail.com"
    SMTP_PORT: int = 587  # Use 587 for TLS, or 465 for SSL
    SMTP_USER: Optional[str] = "vvsnraju.zerokost@gmail.com"
    SMTP_PASSWORD: Optional[str] = "hgjy cafr nshl ytzd"
    SMTP_FROM_EMAIL: Optional[str] = "vvsnraju.zerokost@gmail.com"
    SMTP_FROM_NAME: str = "DMS Notifications"
    SMTP_USE_TLS: bool = True  # Use TLS for port 587
    SMTP_USE_SSL: bool = False  # Use SSL for port 465 (set to True if using port 465)
    EMAIL_ENABLED: bool = True  # Set to True to enable email notifications
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


