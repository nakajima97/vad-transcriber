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
        logger.info(f"[Disconnect] Starting disconnect process for client {client_id}")

        # 接続リストから削除
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(
                f"[Disconnect] Removed client {client_id} from active connections"
            )

        # データカウンターを削除
        if client_id in self.audio_data_count:
            del self.audio_data_count[client_id]

        # 切断時にバッファが残っていれば保存
        if (
            self.in_speech.get(client_id, False)
            and len(self.speech_buffer.get(client_id, b"")) > 0
        ):
            self.segment_count[client_id] = self.segment_count.get(client_id, 0) + 1
            filename = f"segment_{self.segment_count[client_id]:04d}.wav"
            filepath = os.path.join(AUDIO_SEGMENTS_DIR, filename)
            save_pcm_as_wav(self.speech_buffer[client_id], filepath)
            logger.info(f"[VAD] (disconnect) Saved segment: {filename}")

        # 全てのバッファとステートを削除
        for d in [
            self.speech_buffer,
            self.in_speech,
            self.segment_count,
            self.pcm_buffer,
        ]:
            if client_id in d:
                del d[client_id]

        logger.info(f"[Disconnect] Client {client_id} disconnected and cleaned up")

    async def send_json_message(self, data: dict, client_id: str):
        """特定のクライアントにJSONメッセージを送信"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                message = json.dumps(data)
                logger.info(
                    f"[WebSocket] Sending message to client {client_id}: {data.get('type', 'unknown')}"
                )
                await websocket.send_text(message)
                logger.info(
                    f"[WebSocket] Message sent successfully to client {client_id}"
                )
            except Exception as e:
                logger.error(
                    f"[WebSocket] Failed to send message to client {client_id}: {e}"
                )
                logger.error(f"[WebSocket] WebSocket state: {websocket.state}")
                # 接続が切れている場合は接続リストから削除
                logger.warning(f"[WebSocket] Removing disconnected client {client_id}")
                self.disconnect(client_id)
        else:
            logger.warning(
                f"[WebSocket] Client {client_id} not found in active connections"
            )

    async def send_transcription_result(
        self, text: str, client_id: str, segment_id: int
    ):
        """文字起こし結果をクライアントに送信"""
        logger.info(f"send_transcription_result: {text}")
        await self.send_json_message(
            {
                "type": "transcription_result",
                "id": f"{client_id}_{segment_id}",
                "text": text,
                "confidence": 0.95,  # OpenAI APIは通常高い信頼度を持つ
                "timestamp": time.time(),
                "is_final": True,
                "segment_id": segment_id,
            },
            client_id,
        )


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    """WebSocketエンドポイントのメインハンドラー"""
    if not client_id:
        client_id = str(int(time.time() * 1000))  # タイムスタンプベースのID

    logger.info(f"[Connection] New WebSocket connection attempt for client {client_id}")
    await manager.connect(websocket, client_id)
    logger.info(f"[Connection] WebSocket connection established for client {client_id}")

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
        logger.info(
            f"[Connection] WebSocket disconnect detected for client {client_id}"
        )
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(
            f"[Connection] Error in websocket connection for client {client_id}: {e}"
        )
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
                    segment_id = manager.segment_count[client_id]
                    filename = f"segment_{segment_id:04d}.wav"
                    filepath = os.path.join(AUDIO_SEGMENTS_DIR, filename)
                    save_pcm_as_wav(manager.speech_buffer[client_id], filepath)
                    logger.info(f"[VAD] Saved segment: {filename}")

                    # 音声セグメントの長さをチェック（最小1秒 = 16000サンプル = 32000バイト）
                    min_audio_length = SAMPLE_RATE * 1  # 1秒
                    audio_samples = (
                        len(manager.speech_buffer[client_id]) // SAMPLE_WIDTH
                    )

                    if audio_samples < min_audio_length:
                        logger.warning(
                            f"[Audio] Segment {segment_id} too short ({audio_samples} samples < {min_audio_length}), skipping transcription"
                        )
                        await manager.send_json_message(
                            {
                                "type": "transcription_skipped",
                                "segment_id": segment_id,
                                "reason": "Audio segment too short",
                                "duration_seconds": audio_samples / SAMPLE_RATE,
                                "timestamp": time.time(),
                            },
                            client_id,
                        )
                    else:
                        # PCMデータをWAV形式bytesに変換
                        wav_buffer = io.BytesIO()
                        with wave.open(wav_buffer, "wb") as wf:
                            wf.setnchannels(CHANNELS)
                            wf.setsampwidth(SAMPLE_WIDTH)
                            wf.setframerate(SAMPLE_RATE)
                            wf.writeframes(manager.speech_buffer[client_id])
                        wav_bytes = wav_buffer.getvalue()

                        logger.info(
                            f"[Audio] Processing segment {segment_id} ({audio_samples} samples, {audio_samples / SAMPLE_RATE:.2f}s)"
                        )

                        # 文字起こし処理のコールバック関数を定義
                        async def transcription_callback(text: str):
                            logger.info(
                                f"[Transcription] client={client_id} segment={segment_id} text={text}"
                            )
                            await manager.send_transcription_result(
                                text, client_id, segment_id
                            )

                        # エラー処理のコールバック関数を定義
                        async def transcription_error_callback(error: Exception):
                            logger.error(
                                f"[Transcription Error] client={client_id} segment={segment_id} error={error}"
                            )
                            await manager.send_json_message(
                                {
                                    "type": "transcription_error",
                                    "segment_id": segment_id,
                                    "error": str(error),
                                    "timestamp": time.time(),
                                },
                                client_id,
                            )

                        # 非同期で文字起こしを実行
                        async def transcribe_task():
                            try:
                                await transcribe_with_gpt4o(
                                    wav_bytes, callback=transcription_callback
                                )
                            except Exception as e:
                                await transcription_error_callback(e)

                        asyncio.create_task(transcribe_task())

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
