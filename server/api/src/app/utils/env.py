from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")
    
    OPENAI_API_KEY: str
    # 必要に応じて他の環境変数もここに追加
    # 例: DATABASE_URL: str = "sqlite:///:memory:"


settings = Settings()
