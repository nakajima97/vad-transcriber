from app.utils.env import settings
from openai import OpenAI
import tempfile
import asyncio
from typing import Callable, Optional, Union, Awaitable
import logging
import inspect

OPENAI_API_KEY = settings.OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)
logger = logging.getLogger(__name__)


def _transcribe_sync(audio_bytes: bytes, model: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        tmp.flush()
        with open(tmp.name, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=model, file=audio_file, language="ja"
            )
    return transcript.text


async def transcribe_with_gpt4o(
    audio_bytes: bytes,
    callback: Optional[
        Union[Callable[[str], None], Callable[[str], Awaitable[None]]]
    ] = None,
    model: str = "gpt-4o-transcribe",
) -> str:
    """
    OpenAI公式ライブラリで音声データを文字起こしする
    :param audio_bytes: 音声データ（WAV/MP3/FLACなどOpenAI対応形式）
    :param callback: 結果を受け取るコールバック関数（同期・非同期両対応）
    :param model: 使用するモデル名（デフォルト: gpt-4o-transcribe）
    :return: 文字起こしテキスト
    """
    logger.info(f"[Transcription] Starting transcription with model: {model}")
    text = await asyncio.to_thread(_transcribe_sync, audio_bytes, model)
    logger.info(f"[Transcription] Completed with model {model}: {text}")

    if callback:
        # コールバックが非同期関数かどうかを確認
        if inspect.iscoroutinefunction(callback):
            await callback(text)
        else:
            callback(text)

    return text
