from collections import deque
from typing import Optional
from app.adapters.vad import VADAdapter


class VADProcessor:
    """
    Pre-buffering機能付きVADプロセッサ
    発話開始前の音声を保持して頭切れ問題を解決
    """

    def __init__(
        self,
        vad_adapter: VADAdapter,
        sample_rate: int = 16000,
        pre_buffer_duration: float = 0.5,  # 500ms pre-buffer
        threshold: float = 0.3,  # より敏感な閾値
        chunk_size_ms: int = 100,  # 100ms単位で処理
    ):
        self.vad_adapter = vad_adapter
        self.sample_rate = sample_rate
        self.pre_buffer_duration = pre_buffer_duration
        self.threshold = threshold
        self.chunk_size_ms = chunk_size_ms

        # Pre-bufferサイズ計算（100ms単位のチャンク数）
        buffer_chunks = int((pre_buffer_duration * 1000) / chunk_size_ms)
        self.pre_buffer = deque(maxlen=buffer_chunks)

        # 状態管理
        self.is_speaking = False
        self.speech_chunks = []

    def process_audio_chunk(self, pcm_bytes: bytes) -> Optional[bytes]:
        """
        音声チャンクを処理し、完全な発話が検出された場合に音声データを返す

        Returns:
            bytes: 完全な発話音声（Pre-buffer含む）、または None
        """
        if len(pcm_bytes) == 0:
            return None

        # VAD判定
        is_speech, speech_prob = self.vad_adapter.predict(
            pcm_bytes, self.sample_rate, self.threshold
        )

        if is_speech:
            if not self.is_speaking:
                # 発話開始: Pre-bufferの内容を含めて開始
                self.is_speaking = True
                self.speech_chunks = list(self.pre_buffer)  # Pre-bufferをコピー

            # 発話中の音声を追加
            self.speech_chunks.append(pcm_bytes)

        else:
            if self.is_speaking:
                # 発話終了: 蓄積した音声を返す
                self.is_speaking = False
                if self.speech_chunks:
                    # Pre-buffer + 発話音声を結合
                    complete_speech = b"".join(self.speech_chunks)
                    self.speech_chunks = []
                    return complete_speech

        # 非発話時は Pre-buffer に追加
        if not is_speech:
            self.pre_buffer.append(pcm_bytes)

        return None

    def flush(self) -> Optional[bytes]:
        """
        残っている発話データを強制的に返す（ストリーム終了時など）
        """
        if self.is_speaking and self.speech_chunks:
            complete_speech = b"".join(self.speech_chunks)
            self.speech_chunks = []
            self.is_speaking = False
            return complete_speech
        return None

    def reset(self):
        """
        内部状態をリセット
        """
        self.pre_buffer.clear()
        self.speech_chunks = []
        self.is_speaking = False


def vad_predict_enhanced(
    vad_adapter: VADAdapter,
    pcm_bytes: bytes,
    sample_rate: int = 16000,
    threshold: float = 0.3,  # デフォルト閾値を低く設定
) -> tuple[bool, float]:
    """
    Enhanced VAD prediction with lower threshold for better speech detection
    """
    return vad_adapter.predict(pcm_bytes, sample_rate, threshold)
