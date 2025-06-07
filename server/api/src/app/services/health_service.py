from datetime import datetime, UTC
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.schemas.health import (
    DatabaseHealthResponse,
    ApplicationHealthResponse,
    HealthStatus,
    DatabaseStatus,
)


class HealthService:
    """ヘルスチェック関連のビジネスロジック"""

    def __init__(self, db: Session = None):
        self.db = db

    async def check_database_health(self) -> DatabaseHealthResponse:
        """
        データベースの健全性をチェック

        Returns:
            DatabaseHealthResponse: ヘルスチェック結果
        """
        try:
            # シンプルなクエリを実行してDB接続を確認
            self.db.execute(text("SELECT 1"))
            return DatabaseHealthResponse(
                status=HealthStatus.HEALTHY,
                database=DatabaseStatus.CONNECTED,
                message="Database connection is working",
            )
        except Exception as e:
            return DatabaseHealthResponse(
                status=HealthStatus.UNHEALTHY,
                database=DatabaseStatus.DISCONNECTED,
                message=f"Database connection failed: {str(e)}",
            )

    async def check_application_health(self) -> ApplicationHealthResponse:
        """
        アプリケーションの健全性をチェック（DB接続は確認しない）

        Returns:
            ApplicationHealthResponse: アプリケーションヘルスチェック結果
        """
        return ApplicationHealthResponse(
            status=HealthStatus.HEALTHY,
            application=settings.APP_NAME,
            version=settings.APP_VERSION,
            timestamp=datetime.now(UTC),
            message="Application is running successfully",
        )
