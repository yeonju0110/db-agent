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
    
    # Cosmos DB 설정
    cosmos_endpoint: Optional[str] = None
    cosmos_key: Optional[str] = None
    cosmos_database: str = "db-monitoring"
    
    # DB 연결 암호화 키
    db_connection_encryption_key: Optional[str] = None
    
    # Azure Search 설정
    azure_search_endpoint: Optional[str] = None
    azure_search_api_key: Optional[str] = None
    azure_search_index_name: str = "dbschema-tables"
    
    # Azure OpenAI 설정
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_api_version: str = "2024-12-01-preview"
    azure_openai_deployment_name: Optional[str] = None
    azure_openai_embedding_deployment: Optional[str] = None
    
    # 임베딩 설정
    embedding_dim: int = 3072
    
    # pydantic-settings v2 구성
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()

def get_settings() -> Settings:
    """설정 인스턴스 반환"""
    return settings
