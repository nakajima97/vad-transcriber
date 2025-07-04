import json
import logging
import time
import os
import wave
from typing import Dict
import io
import asyncio
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from app.services.vad_chunk import VADProcessor
from app.adapters.transcription import TranscriptionAdapter
from app.adapters.vad import VADAdapter
from app.schemas.websocket import (
    TranscriptionModel,
    WebSocketMessageType,
    ModelSelectionMessage,
)

logger = logging.getLogger(__name__)

AUDIO_SEGMENTS_DIR = "audio_segments"
os.makedirs(AUDIO_SEGMENTS_DIR, exist_ok=True)

VAD_FRAME_SIZE = 512  # 16kHz, 16bit, モノラル: 512サンプル = 1024バイト
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16bit

# VAD設定（検証用）
VAD_SILENCE_TOLERANCE_SECONDS = float(
    os.getenv("VAD_SILENCE_TOLERANCE", "1.5")
)  # 無音許容時間
VAD_SILENCE_FRAME_THRESHOLD = int(
    VAD_SILENCE_TOLERANCE_SECONDS * SAMPLE_RATE / VAD_FRAME_SIZE
)  # フレーム数

logger.info(
    f"[VAD Config] Silence tolerance: {VAD_SILENCE_TOLERANCE_SECONDS}s ({VAD_SILENCE_FRAME_THRESHOLD} frames)"
)


class PendingSegment:
    """保留中のセグメントデータ"""

    def __init__(self, segment_id: int, audio_data: bytes, timestamp: float):
        self.segment_id = segment_id
        self.audio_data = audio_data
        self.timestamp = timestamp
        self.duration = len(audio_data) // SAMPLE_WIDTH / SAMPLE_RATE


class SegmentMerger:
    """
    遅延バッファリング方式でセグメントを結合するクラス
    短いセグメントを一定時間待機して、次のセグメントと結合判定を行う
    """

    def __init__(self, merge_timeout: float = 2.0, min_merge_duration: float = 0.8):
        self.merge_timeout = merge_timeout  # 結合待機時間（秒）
        self.min_merge_duration = min_merge_duration  # この時間未満は結合対象
        self.pending_segments: Dict[
            str, PendingSegment
        ] = {}  # クライアント毎の保留セグメント
        self.pending_tasks: Dict[str, asyncio.Task] = {}  # 遅延処理タスク

    async def process_segment(
        self,
        segment_id: int,
        audio_data: bytes,
        client_id: str,
        transcription_callback,
        error_callback,
    ) -> bool:
        """
        セグメントを処理し、結合するかすぐに文字起こしするかを判定

        Returns:
            bool: True=即座に処理, False=結合待機中
        """
        current_time = time.time()
        duration = len(audio_data) // SAMPLE_WIDTH / SAMPLE_RATE

        # 前の保留セグメントがあるかチェック
        if client_id in self.pending_segments:
            prev_segment = self.pending_segments[client_id]
            time_gap = current_time - prev_segment.timestamp

            # 前のセグメントが短く、時間間隔が短い場合は結合
            if (
                prev_segment.duration < self.min_merge_duration
                and time_gap < self.merge_timeout
            ):
                logger.info(
                    f"[SegmentMerger] Merging segment {prev_segment.segment_id} + {segment_id} "
                    f"(gap: {time_gap:.2f}s, prev_duration: {prev_segment.duration:.2f}s)"
                )

                # 前のタスクをキャンセル
                if client_id in self.pending_tasks:
                    self.pending_tasks[client_id].cancel()
                    del self.pending_tasks[client_id]

                # セグメントを結合
                merged_audio = prev_segment.audio_data + audio_data
                merged_segment = PendingSegment(
                    prev_segment.segment_id, merged_audio, prev_segment.timestamp
                )

                # 結合後のセグメントを処理
                del self.pending_segments[client_id]
                return await self._process_merged_segment(
                    merged_segment, client_id, transcription_callback, error_callback
                )
            else:
                # 前のセグメントを即座に処理（結合しない）
                await self._flush_pending_segment(
                    client_id, transcription_callback, error_callback
                )

        # 現在のセグメントが短い場合は保留
        if duration < self.min_merge_duration:
            logger.info(
                f"[SegmentMerger] Holding segment {segment_id} for potential merge "
                f"(duration: {duration:.2f}s < {self.min_merge_duration}s)"
            )

            self.pending_segments[client_id] = PendingSegment(
                segment_id, audio_data, current_time
            )

            # 遅延処理タスクを開始
            self.pending_tasks[client_id] = asyncio.create_task(
                self._delayed_process(client_id, transcription_callback, error_callback)
            )
            return False
        else:
            # 長いセグメントは即座に処理
            logger.info(
                f"[SegmentMerger] Processing segment {segment_id} immediately (duration: {duration:.2f}s)"
            )
            await transcription_callback(audio_data, segment_id)
            return True

    async def _process_merged_segment(
        self,
        merged_segment: PendingSegment,
        client_id: str,
        transcription_callback,
        error_callback,
    ) -> bool:
        """結合されたセグメントを処理"""
        duration = merged_segment.duration

        # 結合後も短い場合は再度保留
        if duration < self.min_merge_duration:
            logger.info(
                f"[SegmentMerger] Merged segment still short, holding again "
                f"(duration: {duration:.2f}s)"
            )
            self.pending_segments[client_id] = merged_segment
            self.pending_tasks[client_id] = asyncio.create_task(
                self._delayed_process(client_id, transcription_callback, error_callback)
            )
            return False
        else:
            # 十分な長さになったので処理
            logger.info(
                f"[SegmentMerger] Processing merged segment {merged_segment.segment_id} "
                f"(final duration: {duration:.2f}s)"
            )
            await transcription_callback(
                merged_segment.audio_data, merged_segment.segment_id
            )
            return True

    async def _delayed_process(
        self, client_id: str, transcription_callback, error_callback
    ):
        """遅延後にセグメントを処理"""
        try:
            await asyncio.sleep(self.merge_timeout)

            if client_id in self.pending_segments:
                segment = self.pending_segments[client_id]
                logger.info(
                    f"[SegmentMerger] Timeout reached, processing pending segment {segment.segment_id} "
                    f"(duration: {segment.duration:.2f}s)"
                )
                del self.pending_segments[client_id]
                await transcription_callback(segment.audio_data, segment.segment_id)

            if client_id in self.pending_tasks:
                del self.pending_tasks[client_id]

        except asyncio.CancelledError:
            logger.info(
                f"[SegmentMerger] Delayed processing cancelled for client {client_id}"
            )
        except Exception as e:
            logger.error(f"[SegmentMerger] Error in delayed processing: {e}")
            await error_callback(e)

    async def _flush_pending_segment(
        self, client_id: str, transcription_callback, error_callback
    ):
        """保留中のセグメントを即座に処理"""
        if client_id in self.pending_segments:
            segment = self.pending_segments[client_id]
            logger.info(
                f"[SegmentMerger] Flushing pending segment {segment.segment_id}"
            )

            # タスクをキャンセル
            if client_id in self.pending_tasks:
                self.pending_tasks[client_id].cancel()
                del self.pending_tasks[client_id]

            del self.pending_segments[client_id]
            await transcription_callback(segment.audio_data, segment.segment_id)

    async def flush_client(
        self, client_id: str, transcription_callback, error_callback
    ):
        """クライアント切断時に保留中のセグメントを処理"""
        if client_id in self.pending_segments:
            await self._flush_pending_segment(
                client_id, transcription_callback, error_callback
            )

    def cleanup_client(self, client_id: str):
        """クライアント用のリソースをクリーンアップ"""
        if client_id in self.pending_tasks:
            self.pending_tasks[client_id].cancel()
            del self.pending_tasks[client_id]

        if client_id in self.pending_segments:
            del self.pending_segments[client_id]


def save_pcm_as_wav(pcm_bytes: bytes, filepath: str):
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_bytes)


class ConnectionManager:
    """WebSocket接続を管理するクラス"""

    def __init__(
        self,
        transcription_adapter: TranscriptionAdapter,
        vad_adapter: VADAdapter,
        use_vad_processor: bool = False,
        use_segment_merger: bool = True,
    ):
        self.transcription_adapter = transcription_adapter
        self.vad_adapter = vad_adapter
        self.active_connections: Dict[str, WebSocket] = {}
        self.audio_data_count: Dict[str, int] = {}
        # VAD用バッファ・状態
        self.speech_buffer: Dict[str, bytearray] = {}
        self.in_speech: Dict[str, bool] = {}
        self.segment_count: Dict[str, int] = {}
        self.pcm_buffer: Dict[str, bytearray] = {}  # PCMバッファ（VADフレーム分割用）
        self.silence_frame_count: Dict[str, int] = {}  # 連続無音フレーム数

        # クライアント毎のディレクトリ管理
        self.client_directories: Dict[
            str, str
        ] = {}  # クライアントIDごとの保存ディレクトリパス
        self.connection_timestamps: Dict[str, str] = {}  # 接続時刻の記録

        # モデル選択管理
        self.client_models: Dict[
            str, TranscriptionModel
        ] = {}  # クライアント毎の選択モデル

        # 新しいVADProcessor機能（オプション）
        self.use_vad_processor = use_vad_processor
        self.vad_processors: Dict[
            str, VADProcessor
        ] = {}  # クライアント毎のVADProcessor

        # セグメント結合機能
        self.use_segment_merger = use_segment_merger
        self.segment_merger = (
            SegmentMerger(
                merge_timeout=2.0,  # 2秒待機
                min_merge_duration=0.8,  # 0.8秒未満は結合対象
            )
            if use_segment_merger
            else None
        )

    async def connect(self, websocket: WebSocket, client_id: str):
        """新しいクライアント接続を受け入れる"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.audio_data_count[client_id] = 0
        self.speech_buffer[client_id] = bytearray()
        self.in_speech[client_id] = False
        self.segment_count[client_id] = 0
        self.pcm_buffer[client_id] = bytearray()
        self.silence_frame_count[client_id] = 0  # 連続無音フレーム数を初期化

        # デフォルトモデルを設定
        self.client_models[client_id] = TranscriptionModel.GPT_4O_TRANSCRIBE

        # 接続時刻を記録してクライアント専用ディレクトリを作成
        connection_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.connection_timestamps[client_id] = connection_time
        client_dir_name = f"{connection_time}_{client_id}"
        client_dir_path = os.path.join(AUDIO_SEGMENTS_DIR, client_dir_name)
        self.client_directories[client_id] = client_dir_path

        # ディレクトリを作成
        os.makedirs(client_dir_path, exist_ok=True)
        logger.info(f"[Connection] Created audio directory: {client_dir_path}")

        # VADProcessorを使用する場合は初期化
        if self.use_vad_processor:
            self.vad_processors[client_id] = VADProcessor(
                vad_adapter=self.vad_adapter,
                pre_buffer_duration=0.5,  # 500ms pre-buffer
                threshold=0.3,  # より敏感な閾値
                chunk_size_ms=100,  # 100ms単位で処理
            )
            logger.info(f"Client {client_id} connected with VADProcessor enabled")
        else:
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

            # クライアント専用ディレクトリに保存
            client_dir = self.client_directories.get(client_id, AUDIO_SEGMENTS_DIR)
            filepath = os.path.join(client_dir, filename)
            save_pcm_as_wav(self.speech_buffer[client_id], filepath)
            logger.info(f"[VAD] (disconnect) Saved segment: {filepath}")

        # 全てのバッファとステートを削除
        for d in [
            self.speech_buffer,
            self.in_speech,
            self.segment_count,
            self.pcm_buffer,
            self.silence_frame_count,  # 連続無音フレーム数もクリーンアップ
            self.client_directories,  # クライアント専用ディレクトリ情報
            self.connection_timestamps,  # 接続時刻情報
            self.client_models,  # クライアント毎のモデル設定
        ]:
            if client_id in d:
                del d[client_id]

        # VADProcessorも削除
        if client_id in self.vad_processors:
            del self.vad_processors[client_id]

        # SegmentMergerのクリーンアップ（同期的に実行）
        if self.segment_merger:
            try:
                # 保留中のタスクをキャンセルしてクリーンアップ
                self.segment_merger.cleanup_client(client_id)
                logger.info(
                    f"[Disconnect] SegmentMerger cleaned up for client {client_id}"
                )
            except Exception as e:
                logger.error(f"[Disconnect] Error cleaning up SegmentMerger: {e}")

        logger.info(f"[Disconnect] Client {client_id} disconnected and cleaned up")

    async def async_disconnect(self, client_id: str):
        """非同期でクライアント接続を切断し、保留中のセグメントも処理する"""
        logger.info(
            f"[AsyncDisconnect] Starting async disconnect process for client {client_id}"
        )

        # SegmentMergerの保留中セグメントを処理
        if self.segment_merger and client_id in self.segment_merger.pending_segments:
            try:
                # 保留中のセグメントを強制的に処理
                async def final_callback(audio_data, segment_id):
                    """切断時の最終コールバック（ログのみ）"""
                    duration = len(audio_data) // SAMPLE_WIDTH / SAMPLE_RATE
                    logger.info(
                        f"[AsyncDisconnect] Final processing of segment {segment_id} (duration: {duration:.2f}s)"
                    )

                async def final_error_callback(error):
                    logger.error(
                        f"[AsyncDisconnect] Error in final processing: {error}"
                    )

                await self.segment_merger.flush_client(
                    client_id, final_callback, final_error_callback
                )
                logger.info(
                    f"[AsyncDisconnect] Flushed pending segments for client {client_id}"
                )
            except Exception as e:
                logger.error(f"[AsyncDisconnect] Error flushing segments: {e}")

        # 通常の切断処理を実行
        self.disconnect(client_id)
        logger.info(
            f"[AsyncDisconnect] Async disconnect completed for client {client_id}"
        )

    async def set_client_model(self, client_id: str, model: TranscriptionModel):
        """クライアントの音声認識モデルを設定（接続時のみ）"""
        previous_model = self.client_models.get(
            client_id, TranscriptionModel.GPT_4O_TRANSCRIBE
        )
        self.client_models[client_id] = model

        logger.info(
            f"[Model] Client {client_id} model set: {previous_model} -> {model}"
        )

        # 接続時のモデル設定確認メッセージのみ送信（変更通知は不要）
        if previous_model != model:
            logger.info(f"[Model] Model set for client {client_id}: {model}")

    def get_client_model(self, client_id: str) -> TranscriptionModel:
        """クライアントの現在の音声認識モデルを取得"""
        return self.client_models.get(client_id, TranscriptionModel.GPT_4O_TRANSCRIBE)

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
                # 非同期切断処理をタスクとして実行
                asyncio.create_task(self.async_disconnect(client_id))
        else:
            logger.warning(
                f"[WebSocket] Client {client_id} not found in active connections"
            )

    async def send_transcription_result(
        self, text: str, client_id: str, segment_id: int
    ):
        """文字起こし結果をクライアントに送信"""
        logger.info(f"send_transcription_result: {text}")
        current_model = self.get_client_model(client_id)
        await self.send_json_message(
            {
                "type": "transcription_result",
                "id": f"{client_id}_{segment_id}",
                "text": text,
                "confidence": 0.95,  # OpenAI APIは通常高い信頼度を持つ
                "timestamp": time.time(),
                "is_final": True,
                "segment_id": segment_id,
                "model_used": current_model.value,  # Enumの値を文字列として使用
            },
            client_id,
        )


# manager インスタンスは関数レベルで初期化する必要があります
manager = None


def initialize_manager(
    transcription_adapter: TranscriptionAdapter, vad_adapter: VADAdapter
):
    """ConnectionManagerを初期化"""
    global manager
    if manager is None:
        manager = ConnectionManager(
            transcription_adapter=transcription_adapter,
            vad_adapter=vad_adapter,
            use_vad_processor=False,
            use_segment_merger=True,
        )


async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    """WebSocketエンドポイントのメインハンドラー"""
    if not client_id:
        client_id = str(int(time.time() * 1000))  # タイムスタンプベースのID

    logger.info(f"[Connection] New WebSocket connection attempt for client {client_id}")
    await manager.connect(websocket, client_id)
    logger.info(f"[Connection] WebSocket connection established for client {client_id}")

    try:
        # 接続成功メッセージを送信
        current_model = manager.get_client_model(client_id)
        await manager.send_json_message(
            {
                "type": "connection_established",
                "client_id": client_id,
                "message": "WebSocket connection established successfully",
                "model": current_model.value,  # Enumの値を文字列として使用
                "timestamp": time.time(),
            },
            client_id,
        )

        while True:
            try:
                # バイナリまたはテキストメッセージを受信
                message = await websocket.receive()

                if message["type"] == "websocket.receive":
                    if "bytes" in message:
                        # バイナリデータ（音声）の場合
                        audio_data = message["bytes"]
                        await process_audio_data(audio_data, client_id)
                    elif "text" in message:
                        # テキストデータ（JSON）の場合
                        text_data = message["text"]
                        await process_json_message(text_data, client_id)
                    else:
                        logger.warning(
                            f"[WebSocket] Unknown message format from client {client_id}"
                        )
                elif message["type"] == "websocket.disconnect":
                    logger.info(
                        f"[WebSocket] Disconnect message received from client {client_id}"
                    )
                    break

            except Exception as msg_error:
                error_message = str(msg_error)
                logger.error(
                    f"[WebSocket] Error processing message from client {client_id}: {error_message}"
                )

                # WebSocket接続が切断されている場合のエラーメッセージをチェック
                if (
                    'Cannot call "receive" once a disconnect message has been received'
                    in error_message
                    or "disconnect" in error_message.lower()
                    or websocket.client_state == 3  # DISCONNECTED state
                ):
                    logger.info(
                        f"[WebSocket] Client {client_id} disconnected, stopping message processing"
                    )
                    break

                # その他のエラーは継続
                continue

    except WebSocketDisconnect:
        logger.info(
            f"[Connection] WebSocket disconnect detected for client {client_id}"
        )
        await manager.async_disconnect(client_id)
    except Exception as e:
        logger.error(
            f"[Connection] Error in websocket connection for client {client_id}: {e}"
        )
        await manager.async_disconnect(client_id)


async def process_json_message(text_data: str, client_id: str):
    """受信したJSONメッセージを処理"""
    try:
        data = json.loads(text_data)
        message_type = data.get("type")

        logger.info(
            f"[WebSocket] Received JSON message from client {client_id}: {message_type}"
        )

        if message_type == WebSocketMessageType.MODEL_SELECTION:
            # モデル初期設定メッセージの処理（接続時のみ）
            try:
                model_selection = ModelSelectionMessage(**data)
                await manager.set_client_model(client_id, model_selection.model)
                logger.info(
                    f"[Model] Client {client_id} initial model setup: {model_selection.model}"
                )

                # 接続時のモデル設定完了を通知
                await manager.send_json_message(
                    {
                        "type": WebSocketMessageType.CONNECTION_ESTABLISHED,
                        "message": f"音声認識モデル「{model_selection.model.value}」で接続完了",
                        "model": model_selection.model.value,  # Enumの値を文字列として使用
                        "timestamp": time.time(),
                        "client_id": client_id,
                    },
                    client_id,
                )

            except Exception as e:
                logger.error(f"[Model] Error processing initial model setup: {e}")
                await manager.send_json_message(
                    {
                        "type": "error",
                        "message": f"モデル設定エラー: {str(e)}",
                        "timestamp": time.time(),
                    },
                    client_id,
                )
        else:
            logger.warning(f"[WebSocket] Unknown message type: {message_type}")
            await manager.send_json_message(
                {
                    "type": "error",
                    "message": f"不明なメッセージタイプ: {message_type}",
                    "timestamp": time.time(),
                },
                client_id,
            )

    except json.JSONDecodeError as e:
        logger.error(f"[WebSocket] JSON decode error from client {client_id}: {e}")
        await manager.send_json_message(
            {
                "type": "error",
                "message": f"JSON形式エラー: {str(e)}",
                "timestamp": time.time(),
            },
            client_id,
        )
    except Exception as e:
        logger.error(
            f"[WebSocket] Error processing JSON message from client {client_id}: {e}"
        )
        await manager.send_json_message(
            {
                "type": "error",
                "message": f"メッセージ処理エラー: {str(e)}",
                "timestamp": time.time(),
            },
            client_id,
        )


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
            is_speech, speech_prob = manager.vad_adapter.predict(frame)

            silence_count = manager.silence_frame_count.get(client_id, 0)
            logger.info(
                f"[VAD] client={client_id} is_speech={is_speech} prob={speech_prob:.3f} "
                f"silence_frames={silence_count}/{VAD_SILENCE_FRAME_THRESHOLD}"
            )

            if is_speech:
                # 発話検出時の処理
                manager.speech_buffer[client_id].extend(frame)
                manager.in_speech[client_id] = True
                manager.silence_frame_count[client_id] = 0  # 無音カウンタリセット

            else:
                # 無音検出時の処理
                if manager.in_speech.get(client_id, False):
                    # 発話中の無音 - バッファに追加（自然な発話の流れを保持）
                    manager.speech_buffer[client_id].extend(frame)
                    manager.silence_frame_count[client_id] += 1

                    # 閾値に達した場合のみセグメント終了
                    if (
                        manager.silence_frame_count[client_id]
                        >= VAD_SILENCE_FRAME_THRESHOLD
                    ):
                        logger.info(
                            f"[VAD] Silence threshold reached, ending segment for client {client_id}"
                        )

                        # 既存のセグメント終了処理をそのまま実行
                        if len(manager.speech_buffer.get(client_id, b"")) > 0:
                            manager.segment_count[client_id] += 1
                            segment_id = manager.segment_count[client_id]
                            filename = f"segment_{segment_id:04d}.wav"

                            # クライアント専用ディレクトリに保存
                            client_dir = manager.client_directories.get(
                                client_id, AUDIO_SEGMENTS_DIR
                            )
                            filepath = os.path.join(client_dir, filename)
                            save_pcm_as_wav(manager.speech_buffer[client_id], filepath)
                            logger.info(f"[VAD] Saved segment: {filepath}")

                            # 音声セグメントの長さをチェック（最小0.3秒 = 4800サンプル = 9600バイト）
                            min_audio_length = SAMPLE_RATE * 0.3  # 0.3秒
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
                                # セグメント結合機能を使用する場合
                                if (
                                    manager.use_segment_merger
                                    and manager.segment_merger
                                ):
                                    # 音声データのコピー（PCMバイト列）
                                    segment_audio_data = bytes(
                                        manager.speech_buffer[client_id]
                                    )

                                    # セグメント結合処理のコールバック関数を定義
                                    async def segment_transcription_callback(
                                        audio_data: bytes, seg_id: int
                                    ):
                                        """セグメント結合後の文字起こしコールバック"""
                                        # セグメント結合後もファイル保存を行う
                                        filename = f"segment_{seg_id:04d}.wav"
                                        client_dir = manager.client_directories.get(
                                            client_id, AUDIO_SEGMENTS_DIR
                                        )
                                        filepath = os.path.join(client_dir, filename)
                                        save_pcm_as_wav(audio_data, filepath)
                                        logger.info(
                                            f"[SegmentMerger] Saved merged segment: {filepath}"
                                        )

                                        # PCMデータをWAV形式bytesに変換
                                        wav_buffer = io.BytesIO()
                                        with wave.open(wav_buffer, "wb") as wf:
                                            wf.setnchannels(CHANNELS)
                                            wf.setsampwidth(SAMPLE_WIDTH)
                                            wf.setframerate(SAMPLE_RATE)
                                            wf.writeframes(audio_data)
                                        wav_bytes = wav_buffer.getvalue()

                                        samples = len(audio_data) // SAMPLE_WIDTH
                                        duration = samples / SAMPLE_RATE
                                        logger.info(
                                            f"[Audio] Processing segment {seg_id} ({samples} samples, {duration:.2f}s)"
                                        )

                                        # 文字起こし処理
                                        async def transcription_callback(text: str):
                                            selected_model = manager.get_client_model(
                                                client_id
                                            )
                                            logger.info(
                                                f"[Transcription] client={client_id} segment={seg_id} model={selected_model.value} text={text}"
                                            )
                                            await manager.send_transcription_result(
                                                text, client_id, seg_id
                                            )

                                        async def transcription_error_callback(
                                            error: Exception,
                                        ):
                                            current_model = manager.get_client_model(
                                                client_id
                                            )
                                            logger.error(
                                                f"[Transcription Error] client={client_id} segment={seg_id} model={current_model.value} error={error}"
                                            )
                                            await manager.send_json_message(
                                                {
                                                    "type": "transcription_error",
                                                    "segment_id": seg_id,
                                                    "error": str(error),
                                                    "model_used": current_model.value,  # Enumの値を文字列として使用
                                                    "timestamp": time.time(),
                                                },
                                                client_id,
                                            )

                                        # 非同期で文字起こしを実行
                                        async def transcribe_task():
                                            try:
                                                # クライアントの選択モデルを使用
                                                selected_model = (
                                                    manager.get_client_model(client_id)
                                                )
                                                await manager.transcription_adapter.transcribe(
                                                    wav_bytes,
                                                    model=selected_model.value,  # Enumの値を文字列として使用
                                                    callback=transcription_callback,
                                                )
                                            except Exception as e:
                                                await transcription_error_callback(e)

                                        asyncio.create_task(transcribe_task())

                                    async def segment_error_callback(error: Exception):
                                        """セグメント結合エラーコールバック"""
                                        logger.error(
                                            f"[SegmentMerger Error] client={client_id} error={error}"
                                        )
                                        await manager.send_json_message(
                                            {
                                                "type": "segment_merge_error",
                                                "error": str(error),
                                                "timestamp": time.time(),
                                            },
                                            client_id,
                                        )

                                    # セグメント結合処理を実行
                                    processed_immediately = (
                                        await manager.segment_merger.process_segment(
                                            segment_id,
                                            segment_audio_data,
                                            client_id,
                                            segment_transcription_callback,
                                            segment_error_callback,
                                        )
                                    )

                                    if processed_immediately:
                                        logger.info(
                                            f"[SegmentMerger] Segment {segment_id} processed immediately"
                                        )
                                    else:
                                        logger.info(
                                            f"[SegmentMerger] Segment {segment_id} held for potential merge"
                                        )

                                else:
                                    # 従来の処理（セグメント結合なし）
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
                                        selected_model = manager.get_client_model(
                                            client_id
                                        )
                                        logger.info(
                                            f"[Transcription] client={client_id} segment={segment_id} model={selected_model.value} text={text}"
                                        )
                                        await manager.send_transcription_result(
                                            text, client_id, segment_id
                                        )

                                    # エラー処理のコールバック関数を定義
                                    async def transcription_error_callback(
                                        error: Exception,
                                    ):
                                        current_model = manager.get_client_model(
                                            client_id
                                        )
                                        logger.error(
                                            f"[Transcription Error] client={client_id} segment={segment_id} model={current_model.value} error={error}"
                                        )
                                        await manager.send_json_message(
                                            {
                                                "type": "transcription_error",
                                                "segment_id": segment_id,
                                                "error": str(error),
                                                "model_used": current_model.value,  # Enumの値を文字列として使用
                                                "timestamp": time.time(),
                                            },
                                            client_id,
                                        )

                                    # 非同期で文字起こしを実行
                                    async def transcribe_task():
                                        try:
                                            # クライアントの選択モデルを使用
                                            selected_model = manager.get_client_model(
                                                client_id
                                            )
                                            await manager.transcription_adapter.transcribe(
                                                wav_bytes,
                                                model=selected_model.value,  # Enumの値を文字列として使用
                                                callback=transcription_callback,
                                            )
                                        except Exception as e:
                                            await transcription_error_callback(e)

                                    asyncio.create_task(transcribe_task())

                            # 状態リセット
                            manager.speech_buffer[client_id].clear()
                            manager.silence_frame_count[client_id] = 0

                        manager.in_speech[client_id] = False
                    # else: まだ閾値に達していない → 区切らずに継続
                # else: 発話開始前の無音 → 何もしない
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
