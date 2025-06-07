from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dummy():
    response = client.get("/")
    assert response.status_code == 200


def test_health_check_database():
    response = client.get("/api/v1/health/db")
    # データベースが起動していない場合は503エラーが想定される
    assert response.status_code in [200, 503]


def test_health_check_application():
    response = client.get("/api/v1/health")
    # アプリケーション単体のヘルスチェックは常に200になる想定
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["application"] == "FastAPI Template"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data
    assert "message" in data
