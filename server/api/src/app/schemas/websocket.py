from enum import Enum
from typing import Union, Literal
from pydantic import BaseModel, Field


class TranscriptionModel(str, Enum):
    """利用可能な音声認識モデル"""

    WHISPER_1 = "whisper-1"
    GPT_4O_TRANSCRIBE = "gpt-4o-transcribe"
    GPT_4O_MINI_TRANSCRIBE = "gpt-4o-mini-transcribe"


class WebSocketMessageType(str, Enum):
    """WebSocketメッセージタイプ"""

    # クライアント → サーバー
    MODEL_SELECTION = "model_selection"

    # サーバー → クライアント
    CONNECTION_ESTABLISHED = "connection_established"
    TRANSCRIPTION_RESULT = "transcription_result"
    VAD_RESULT = "vad_result"
    TRANSCRIPTION_ERROR = "transcription_error"
    TRANSCRIPTION_SKIPPED = "transcription_skipped"
    AUDIO_RECEIVED = "audio_received"
    STATISTICS = "statistics"
    ERROR = "error"
    SEGMENT_MERGE_ERROR = "segment_merge_error"


class BaseWebSocketMessage(BaseModel):
    """WebSocketメッセージの基底クラス"""

    type: WebSocketMessageType
    timestamp: float


# クライアント → サーバー メッセージ
class ModelSelectionMessage(BaseWebSocketMessage):
    """モデル選択メッセージ"""

    type: Literal[WebSocketMessageType.MODEL_SELECTION] = (
        WebSocketMessageType.MODEL_SELECTION
    )
    model: TranscriptionModel = Field(..., description="選択された音声認識モデル")


# サーバー → クライアント メッセージ
class ConnectionEstablishedMessage(BaseWebSocketMessage):
    """接続確立メッセージ"""

    type: Literal[WebSocketMessageType.CONNECTION_ESTABLISHED] = (
        WebSocketMessageType.CONNECTION_ESTABLISHED
    )
    client_id: str = Field(..., description="クライアントID")
    message: str = Field(..., description="接続確立メッセージ")
    model: TranscriptionModel = Field(..., description="設定されているモデル")


class TranscriptionResultMessage(BaseWebSocketMessage):
    """文字起こし結果メッセージ"""

    type: Literal[WebSocketMessageType.TRANSCRIPTION_RESULT] = (
        WebSocketMessageType.TRANSCRIPTION_RESULT
    )
    id: str = Field(..., description="結果ID")
    text: str = Field(..., description="文字起こし結果テキスト")
    confidence: float = Field(..., description="信頼度", ge=0.0, le=1.0)
    is_final: bool = Field(..., description="最終結果かどうか")
    segment_id: int = Field(..., description="セグメントID")
    model_used: TranscriptionModel = Field(..., description="使用されたモデル")


class VADResultMessage(BaseWebSocketMessage):
    """VAD結果メッセージ"""

    type: Literal[WebSocketMessageType.VAD_RESULT] = WebSocketMessageType.VAD_RESULT
    is_speech: bool = Field(..., description="音声検出結果")
    confidence: float = Field(..., description="検出信頼度", ge=0.0, le=1.0)


class TranscriptionErrorMessage(BaseWebSocketMessage):
    """文字起こしエラーメッセージ"""

    type: Literal[WebSocketMessageType.TRANSCRIPTION_ERROR] = (
        WebSocketMessageType.TRANSCRIPTION_ERROR
    )
    segment_id: int = Field(..., description="エラーが発生したセグメントID")
    error: str = Field(..., description="エラーメッセージ")
    model_used: TranscriptionModel = Field(..., description="エラーが発生したモデル")


class TranscriptionSkippedMessage(BaseWebSocketMessage):
    """文字起こしスキップメッセージ"""

    type: Literal[WebSocketMessageType.TRANSCRIPTION_SKIPPED] = (
        WebSocketMessageType.TRANSCRIPTION_SKIPPED
    )
    segment_id: int = Field(..., description="スキップされたセグメントID")
    reason: str = Field(..., description="スキップ理由")
    duration_seconds: float = Field(..., description="音声の長さ（秒）")


class AudioReceivedMessage(BaseWebSocketMessage):
    """音声受信確認メッセージ"""

    type: Literal[WebSocketMessageType.AUDIO_RECEIVED] = (
        WebSocketMessageType.AUDIO_RECEIVED
    )
    data_size: int = Field(..., description="受信データサイズ（バイト）")
    packet_count: int = Field(..., description="パケット数")
    message: str = Field(..., description="受信確認メッセージ")


class StatisticsMessage(BaseWebSocketMessage):
    """統計情報メッセージ"""

    type: Literal[WebSocketMessageType.STATISTICS] = WebSocketMessageType.STATISTICS
    total_packets: int = Field(..., description="総パケット数")
    message: str = Field(..., description="統計メッセージ")


class ErrorMessage(BaseWebSocketMessage):
    """エラーメッセージ"""

    type: Literal[WebSocketMessageType.ERROR] = WebSocketMessageType.ERROR
    message: str = Field(..., description="エラーメッセージ")


class SegmentMergeErrorMessage(BaseWebSocketMessage):
    """セグメント結合エラーメッセージ"""

    type: Literal[WebSocketMessageType.SEGMENT_MERGE_ERROR] = (
        WebSocketMessageType.SEGMENT_MERGE_ERROR
    )
    error: str = Field(..., description="エラーメッセージ")


# Union型でメッセージタイプを統合
ClientMessage = Union[ModelSelectionMessage,]

ServerMessage = Union[
    ConnectionEstablishedMessage,
    TranscriptionResultMessage,
    VADResultMessage,
    TranscriptionErrorMessage,
    TranscriptionSkippedMessage,
    AudioReceivedMessage,
    StatisticsMessage,
    ErrorMessage,
    SegmentMergeErrorMessage,
]

WebSocketMessage = Union[ClientMessage, ServerMessage]
