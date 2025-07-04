import tempfile
import asyncio
import logging
import inspect
from typing import Optional, Union, Callable, Awaitable
from openai import OpenAI
from .base import TranscriptionAdapter


logger = logging.getLogger(__name__)


class OpenAITranscriptionAdapter(TranscriptionAdapter):
    """
    OpenAI API を使用した音声文字起こしアダプター
    """

    def __init__(self, api_key: str, **kwargs):
        super().__init__(**kwargs)
        self.client = OpenAI(api_key=api_key)
        self.supported_models = [
            "gpt-4o-transcribe",
            "whisper-1",
        ]

    async def health_check(self) -> bool:
        """
        OpenAI APIの健康状態をチェック
        """
        try:
            # モデル一覧を取得してAPIが正常に動作しているかチェック
            models = await asyncio.to_thread(self.client.models.list)
            return len(models.data) > 0
        except Exception as e:
            logger.error(f"OpenAI API health check failed: {e}")
            return False

    def _transcribe_sync(self, audio_bytes: bytes, model: str, language: str) -> str:
        """
        同期的な文字起こし処理
        """
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            with open(tmp.name, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=model, file=audio_file, language=language
                )
        return transcript.text

    async def transcribe(
        self,
        audio_bytes: bytes,
        model: str = "gpt-4o-transcribe",
        language: str = "ja",
        callback: Optional[
            Union[Callable[[str], None], Callable[[str], Awaitable[None]]]
        ] = None,
    ) -> str:
        """
        音声データを文字起こし
        """
        if model not in self.supported_models:
            raise ValueError(
                f"Unsupported model: {model}. Supported models: {self.supported_models}"
            )

        logger.info(
            f"[OpenAI Transcription] Starting transcription with model: {model}"
        )

        text = await asyncio.to_thread(
            self._transcribe_sync, audio_bytes, model, language
        )

        logger.info(f"[OpenAI Transcription] Completed with model {model}: {text}")

        if callback:
            if inspect.iscoroutinefunction(callback):
                await callback(text)
            else:
                callback(text)

        return text

    def get_supported_models(self) -> list[str]:
        """
        サポートされているモデルの一覧を取得
        """
        return self.supported_models.copy()


class MockTranscriptionAdapter(TranscriptionAdapter):
    """
    テスト用のモック文字起こしアダプター
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.supported_models = ["mock-model"]

    async def health_check(self) -> bool:
        """
        常に正常を返す
        """
        return True

    async def transcribe(
        self,
        audio_bytes: bytes,
        model: str = "mock-model",
        language: str = "ja",
        callback: Optional[
            Union[Callable[[str], None], Callable[[str], Awaitable[None]]]
        ] = None,
    ) -> str:
        """
        固定の文字起こし結果を返す
        """
        text = "これはテスト用の文字起こし結果です"

        if callback:
            if inspect.iscoroutinefunction(callback):
                await callback(text)
            else:
                callback(text)

        return text

    def get_supported_models(self) -> list[str]:
        """
        サポートされているモデルの一覧を取得
        """
        return self.supported_models.copy()
