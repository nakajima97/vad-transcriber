import torch
import numpy as np
import os
import logging
# from typing import Optional
from .base import VADAdapter


logger = logging.getLogger(__name__)


class SileroVADAdapter(VADAdapter):
    """
    Silero VAD を使用した音声検出アダプター
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._model = None
        self._utils = None
        self._initialize_model()

    def _initialize_model(self):
        """
        Silero VAD モデルを初期化
        """
        try:
            # cSpell:ignore snakers silero
            self._model, self._utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad", 
                model="silero_vad", 
                force_reload=False
            )
            logger.info("Silero VAD model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD model: {e}")
            raise

    async def health_check(self) -> bool:
        """
        VAD モデルの健康状態をチェック
        """
        try:
            # テスト用の音声データで動作確認
            test_audio = np.random.rand(1024).astype(np.float32)
            test_tensor = torch.from_numpy(test_audio)
            result = self._model(test_tensor, 16000)
            return isinstance(result.item(), float)
        except Exception as e:
            logger.error(f"VAD health check failed: {e}")
            return False

    def _pcm_bytes_to_float32(self, pcm_bytes: bytes) -> np.ndarray:  # cSpell:ignore ndarray
        """
        16bit PCMバイト列をfloat32正規化配列に変換
        """
        audio = np.frombuffer(pcm_bytes, dtype=np.int16)  # cSpell:ignore frombuffer
        audio = audio.astype(np.float32) / 32768.0
        return audio

    def predict(
        self,
        audio_bytes: bytes,
        sample_rate: int = 16000,
        threshold: float = 0.5,
    ) -> tuple[bool, float]:
        """
        音声検出を実行
        """
        audio = self._pcm_bytes_to_float32(audio_bytes)
        if len(audio) == 0:
            return False, 0.0
        
        audio_tensor = torch.from_numpy(audio)
        speech_prob = self._model(audio_tensor, sample_rate).item()
        is_speech = speech_prob > threshold
        
        return is_speech, speech_prob

    def get_optimal_chunk_size(self) -> int:
        """
        最適なチャンクサイズを取得
        Silero VAD は 512 サンプル (16bit PCM で 1024 バイト) が推奨
        """
        return 1024  # 512 samples * 2 bytes per sample


class MockVADAdapter(VADAdapter):
    """
    テスト用のモック VAD アダプター
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fixed_probability = kwargs.get("fixed_probability", 0.8)

    async def health_check(self) -> bool:
        """
        常に正常を返す
        """
        return True

    def predict(
        self,
        audio_bytes: bytes,
        sample_rate: int = 16000,
        threshold: float = 0.5,
    ) -> tuple[bool, float]:
        """
        固定の音声検出結果を返す
        """
        if len(audio_bytes) == 0:
            return False, 0.0
        
        is_speech = self.fixed_probability > threshold
        return is_speech, self.fixed_probability

    def get_optimal_chunk_size(self) -> int:
        """
        テスト用の固定サイズを返す
        """
        return 1024


def create_vad_adapter(testing: bool = False, **kwargs) -> VADAdapter:
    """
    環境に応じて適切な VAD アダプターを生成
    """
    if testing or os.environ.get("TESTING") == "true":
        return MockVADAdapter(**kwargs)
    else:
        return SileroVADAdapter(**kwargs)