from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.health_service import HealthService


def get_health_service(db: Session = Depends(get_db)) -> HealthService:
    """データベースヘルスチェック用HealthServiceの依存性注入"""
    return HealthService(db)


def get_app_health_service() -> HealthService:
    """アプリケーションヘルスチェック用HealthServiceの依存性注入（DBなし）"""
    return HealthService()
