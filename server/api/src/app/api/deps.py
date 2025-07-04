from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.health_service import HealthService
from app.adapters.transcription import (
    OpenAITranscriptionAdapter,
    MockTranscriptionAdapter,
)
from app.adapters.vad import create_vad_adapter
from app.utils.env import settings
import os


def get_health_service(db: Session = Depends(get_db)) -> HealthService:
    """データベースヘルスチェック用HealthServiceの依存性注入"""
    return HealthService(db)


def get_app_health_service() -> HealthService:
    """アプリケーションヘルスチェック用HealthServiceの依存性注入（DBなし）"""
    return HealthService()


def get_transcription_adapter() -> OpenAITranscriptionAdapter:
    """文字起こしアダプターの依存性注入"""
    if os.environ.get("TESTING") == "true":
        return MockTranscriptionAdapter()
    return OpenAITranscriptionAdapter(api_key=settings.OPENAI_API_KEY)


def get_vad_adapter():
    """VADアダプターの依存性注入"""
    testing = os.environ.get("TESTING") == "true"
    return create_vad_adapter(testing=testing)
