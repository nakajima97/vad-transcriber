import torch
import numpy as np
from collections import deque
from typing import Optional
import os

# テスト環境でのモック対応
if os.environ.get("TESTING") == "true":
    # テスト用のモックモデル
    class MockVADModel:
        def __call__(self, audio_tensor, sample_rate):
            # テスト用の固定値を返す
            return torch.tensor(0.8)  # 高い音声確率

    model = MockVADModel()
    utils = (None, None, None, None, None)
    (get_speech_timestamps, _, read_audio, _, _) = utils
else:
    # 本番環境でのSilero VADモデルのロード
    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad", model="silero_vad", force_reload=False
    )
    (get_speech_timestamps, _, read_audio, _, _) = utils


def pcm_bytes_to_float32(pcm_bytes: bytes) -> np.ndarray:
    """
    16bit PCMバイト列をfloat32正規化配列に変換
    """
    audio = np.frombuffer(pcm_bytes, dtype=np.int16)
    audio = audio.astype(np.float32) / 32768.0
    return audio


def vad_predict(
    pcm_bytes: bytes, sample_rate: int = 16000, threshold: float = 0.5
) -> tuple[bool, float]:
    """
    PCMバイト列をVAD判定し、(is_speech, speech_prob)を返す
    """
    audio = pcm_bytes_to_float32(pcm_bytes)
    if len(audio) == 0:
        return False, 0.0
    audio_tensor = torch.from_numpy(audio)
    speech_prob = model(audio_tensor, sample_rate).item()
    is_speech = speech_prob > threshold
    return is_speech, speech_prob


class VADProcessor:
    """
    Pre-buffering機能付きVADプロセッサ
    発話開始前の音声を保持して頭切れ問題を解決
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        pre_buffer_duration: float = 0.5,  # 500ms pre-buffer
        threshold: float = 0.3,  # より敏感な閾値
        chunk_size_ms: int = 100,  # 100ms単位で処理
    ):
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
        is_speech, speech_prob = vad_predict(
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
    pcm_bytes: bytes,
    sample_rate: int = 16000,
    threshold: float = 0.3,  # デフォルト閾値を低く設定
) -> tuple[bool, float]:
    """
    Enhanced VAD prediction with lower threshold for better speech detection
    """
    return vad_predict(pcm_bytes, sample_rate, threshold)
