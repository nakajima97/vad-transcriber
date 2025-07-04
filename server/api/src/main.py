import logging
from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.websocket.handlers import websocket_endpoint, initialize_manager
from app.api.deps import get_transcription_adapter, get_vad_adapter

app = FastAPI(
    title="VAD Transcriber API",
    description="リアルタイム音声認識とVADのためのWebSocket API",
    version="0.1.0",
)

# CORS設定（フロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],  # Next.jsデフォルトポート
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.DEBUG,
)


@app.get("/")
def read_root():
    return {
        "message": "VAD Transcriber API",
        "status": "running",
        "websocket_endpoint": "/ws",
    }


# WebSocketエンドポイント
@app.websocket("/ws")
async def websocket_route(
    websocket: WebSocket, 
    transcription_adapter=Depends(get_transcription_adapter),
    vad_adapter=Depends(get_vad_adapter)
):
    # アダプターを使用してConnectionManagerを初期化
    initialize_manager(transcription_adapter, vad_adapter)
    await websocket_endpoint(websocket)


# API v1のルーターを含める
app.include_router(api_router, prefix="/api/v1")
