from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class HealthStatus(str, Enum):
    """ヘルスステータスの列挙型"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class DatabaseStatus(str, Enum):
    """データベースステータスの列挙型"""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class DatabaseHealthResponse(BaseModel):
    """データベースヘルスチェックのレスポンスモデル"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "database": "connected",
                "message": "Database connection is working",
            }
        }
    )

    status: HealthStatus = Field(..., description="ヘルスチェックの結果ステータス")
    database: DatabaseStatus = Field(..., description="データベース接続の状態")
    message: str = Field(
        ...,
        description="ヘルスチェックの詳細メッセージ",
    )


class DatabaseHealthErrorResponse(BaseModel):
    """データベースヘルスチェックエラー時のレスポンスモデル (HTTPException用)"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": {
                    "status": "unhealthy",
                    "database": "disconnected",
                    "message": "Database connection failed: connection timeout",
                }
            }
        }
    )

    detail: dict = Field(
        ...,
        description="エラーの詳細情報",
    )


class ApplicationHealthResponse(BaseModel):
    """アプリケーションヘルスチェックのレスポンスモデル"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "application": "FastAPI Template",
                "version": "0.1.0",
                "timestamp": "2024-01-01T12:00:00.000Z",
                "message": "Application is running successfully",
            }
        }
    )

    status: HealthStatus = Field(..., description="アプリケーションのヘルスステータス")
    application: str = Field(..., description="アプリケーション名")
    version: str = Field(..., description="アプリケーションバージョン")
    timestamp: datetime = Field(..., description="ヘルスチェック実行時刻")
    message: str = Field(
        ...,
        description="ヘルスチェックメッセージ",
    )
