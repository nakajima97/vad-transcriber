from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    # 必要に応じて他の環境変数もここに追加
    # 例: DATABASE_URL: str = "sqlite:///:memory:"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings() 