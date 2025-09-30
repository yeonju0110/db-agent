from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import Optional

class Settings(BaseSettings):
    # 환경 설정
    environment: str = "development"
    debug: bool = True
    
    # 고객사 DB 설정
    test_client_db_host: str
    test_client_db_name: str
    test_client_db_user: str
    test_client_db_password: SecretStr
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
    cosmos_key: Optional[SecretStr] = None
    cosmos_database: str
    
    # DB 연결 암호화 키
    db_connection_encryption_key: Optional[SecretStr] = None
    
    # Azure Search 설정
    azure_search_endpoint: Optional[str] = None
    azure_search_api_key: Optional[SecretStr] = None
    azure_search_index_name: str = "dbschema-tables"
    
    # Azure OpenAI 설정
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[SecretStr] = None
    azure_openai_api_version: str = "2024-12-01-preview"
    azure_openai_deployment_name: Optional[str] = None
    azure_openai_embedding_deployment: Optional[str] = None
    
    # 임베딩 설정
    embedding_dim: int = 3072
    
    # 스케줄러 설정
    scheduler_interval_minutes: int = 60
    scheduler_default_interval_minutes: int = 60
    
    # 테넌트 설정
    default_tenant_id: str = "default"
    default_tenant_name: str = "default_tenant"
    
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
