from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_health_service, get_app_health_service
from app.services.health_service import HealthService
from app.schemas.health import (
    DatabaseHealthResponse,
    DatabaseHealthErrorResponse,
    ApplicationHealthResponse,
    HealthStatus,
)

router = APIRouter()


@router.get(
    "/health/db",
    summary="Health Check DB",
    description="データベースへの疎通確認用ヘルスチェックエンドポイント",
    response_model=DatabaseHealthResponse,
    responses={
        200: {"description": "データベース接続が正常", "model": DatabaseHealthResponse},
        503: {
            "description": "データベース接続に失敗",
            "model": DatabaseHealthErrorResponse,
        },
    },
)
async def health_check_database(
    health_service: HealthService = Depends(get_health_service),
):
    result = await health_service.check_database_health()

    if result.status == HealthStatus.UNHEALTHY:
        raise HTTPException(status_code=503, detail=result.dict())

    return result


@router.get(
    "/health",
    summary="Health Check Application",
    description="アプリケーション単体の疎通確認用ヘルスチェックエンドポイント（データベース接続は確認しない）",
    response_model=ApplicationHealthResponse,
)
async def health_check_application(
    health_service: HealthService = Depends(get_app_health_service),
):
    """
    アプリケーション単体のヘルスチェック
    データベース接続は確認せず、FastAPIアプリケーション自体の動作確認のみ
    """
    return await health_service.check_application_health()
