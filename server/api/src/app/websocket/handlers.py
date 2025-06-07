import asyncio
import json
import logging
import time
from typing import Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket接続を管理するクラス"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.audio_data_count: Dict[str, int] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """新しいクライアント接続を受け入れる"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.audio_data_count[client_id] = 0
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        """クライアント接続を切断する"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.audio_data_count:
            del self.audio_data_count[client_id]
        logger.info(f"Client {client_id} disconnected")

    async def send_json_message(self, data: dict, client_id: str):
        """特定のクライアントにJSONメッセージを送信"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            if websocket.state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps(data))


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    """WebSocketエンドポイントのメインハンドラー"""
    if not client_id:
        client_id = str(int(time.time() * 1000))  # タイムスタンプベースのID

    await manager.connect(websocket, client_id)

    try:
        # 接続成功メッセージを送信
        await manager.send_json_message(
            {
                "type": "connection_established",
                "client_id": client_id,
                "message": "WebSocket connection established successfully",
                "timestamp": time.time(),
            },
            client_id,
        )

        while True:
            # バイナリデータ（音声）を受信
            audio_data = await websocket.receive_bytes()

            # 音声データを処理
            await process_audio_data(audio_data, client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error in websocket connection for client {client_id}: {e}")
        manager.disconnect(client_id)


async def process_audio_data(audio_data: bytes, client_id: str):
    """受信した音声データを処理する（シンプルな確認のみ）"""
    try:
        # 受信データをカウント
        if client_id in manager.audio_data_count:
            manager.audio_data_count[client_id] += 1

        data_size = len(audio_data)
        data_count = manager.audio_data_count.get(client_id, 0)

        logger.info(
            f"Received audio data from {client_id}: {data_size} bytes (total packets: {data_count})"
        )

        # 受信確認をクライアントに送信
        await manager.send_json_message(
            {
                "type": "audio_received",
                "timestamp": time.time(),
                "data_size": data_size,
                "packet_count": data_count,
                "message": f"Audio data received successfully ({data_size} bytes)",
            },
            client_id,
        )

        # 10回に1回、詳細な統計を送信
        if data_count % 10 == 0:
            await manager.send_json_message(
                {
                    "type": "statistics",
                    "timestamp": time.time(),
                    "total_packets": data_count,
                    "message": f"Total audio packets received: {data_count}",
                },
                client_id,
            )

    except Exception as e:
        logger.error(f"Error processing audio data for client {client_id}: {e}")
        await manager.send_json_message(
            {
                "type": "error",
                "message": f"Audio processing error: {str(e)}",
                "timestamp": time.time(),
            },
            client_id,
        )
