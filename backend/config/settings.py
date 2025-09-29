from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # 환경 설정
    environment: str = "development"
    debug: bool = True
    
    # 고객사 DB 설정
    test_client_db_host: str
    test_client_db_name: str
    test_client_db_user: str
    test_client_db_password: str
    test_client_db_port: int = 5432
    test_client_db_type: str = "postgres"

    # 로깅 설정
    log_level: str = "INFO"
    azure_appinsights_connection_string: Optional[str] = None
    
    # API 설정
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # pydantic-settings v2 구성
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
