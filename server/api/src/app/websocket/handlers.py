import json
import logging
import time
import os
import wave
from typing import Dict
import io
import asyncio

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from app.services.vad_chunk import vad_predict
from app.utils.openai_transcribe import transcribe_with_gpt4o

logger = logging.getLogger(__name__)

AUDIO_SEGMENTS_DIR = "audio_segments"
os.makedirs(AUDIO_SEGMENTS_DIR, exist_ok=True)

VAD_FRAME_SIZE = 512  # 16kHz, 16bit, モノラル: 512サンプル = 1024バイト
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16bit


def save_pcm_as_wav(pcm_bytes: bytes, filepath: str):
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_bytes)


class ConnectionManager:
    """WebSocket接続を管理するクラス"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.audio_data_count: Dict[str, int] = {}
        # VAD用バッファ・状態
        self.speech_buffer: Dict[str, bytearray] = {}
        self.in_speech: Dict[str, bool] = {}
        self.segment_count: Dict[str, int] = {}
        self.pcm_buffer: Dict[str, bytearray] = {}  # PCMバッファ（VADフレーム分割用）

    async def connect(self, websocket: WebSocket, client_id: str):
        """新しいクライアント接続を受け入れる"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.audio_data_count[client_id] = 0
        self.speech_buffer[client_id] = bytearray()
        self.in_speech[client_id] = False
        self.segment_count[client_id] = 0
        self.pcm_buffer[client_id] = bytearray()
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        """クライアント接続を切断する"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.audio_data_count:
            del self.audio_data_count[client_id]
        # 切断時にバッファが残っていれば保存
        if (
            self.in_speech.get(client_id, False)
            and len(self.speech_buffer.get(client_id, b"")) > 0
        ):
            self.segment_count[client_id] += 1
            filename = f"segment_{self.segment_count[client_id]:04d}.wav"
            filepath = os.path.join(AUDIO_SEGMENTS_DIR, filename)
            save_pcm_as_wav(self.speech_buffer[client_id], filepath)
            logger.info(f"[VAD] (disconnect) Saved segment: {filename}")
        for d in [
            self.speech_buffer,
            self.in_speech,
            self.segment_count,
            self.pcm_buffer,
        ]:
            if client_id in d:
                del d[client_id]
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
    """受信した音声データをVAD判定し、区間保存・ログ出力"""
    try:
        # 受信データをカウント
        if client_id in manager.audio_data_count:
            manager.audio_data_count[client_id] += 1

        data_size = len(audio_data)
        data_count = manager.audio_data_count.get(client_id, 0)

        # PCMバッファに追加
        manager.pcm_buffer[client_id].extend(audio_data)
        buf = manager.pcm_buffer[client_id]
        frame_bytes = VAD_FRAME_SIZE * 2  # 16bit=2byte
        offset = 0
        while len(buf) - offset >= frame_bytes:
            frame = buf[offset : offset + frame_bytes]
            is_speech, speech_prob = vad_predict(frame)
            logger.info(
                f"[VAD] client={client_id} is_speech={is_speech} prob={speech_prob:.3f} size={frame_bytes}"
            )
            if is_speech:
                manager.speech_buffer[client_id].extend(frame)
                manager.in_speech[client_id] = True
            else:
                if (
                    manager.in_speech.get(client_id, False)
                    and len(manager.speech_buffer.get(client_id, b"")) > 0
                ):
                    manager.segment_count[client_id] += 1
                    filename = f"segment_{manager.segment_count[client_id]:04d}.wav"
                    filepath = os.path.join(AUDIO_SEGMENTS_DIR, filename)
                    save_pcm_as_wav(manager.speech_buffer[client_id], filepath)
                    logger.info(f"[VAD] Saved segment: {filename}")

                    # PCMデータをWAV形式bytesに変換
                    wav_buffer = io.BytesIO()
                    with wave.open(wav_buffer, "wb") as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(SAMPLE_WIDTH)
                        wf.setframerate(SAMPLE_RATE)
                        wf.writeframes(manager.speech_buffer[client_id])
                    wav_bytes = wav_buffer.getvalue()
                    # 非同期でtranscribe_with_gpt4oを呼び出し
                    asyncio.create_task(transcribe_with_gpt4o(wav_bytes))

                    manager.speech_buffer[client_id].clear()
                manager.in_speech[client_id] = False
            offset += frame_bytes
        # 余りはバッファに残す
        manager.pcm_buffer[client_id] = buf[offset:]

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
