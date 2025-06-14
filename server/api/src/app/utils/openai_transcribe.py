from app.utils.env import settings
from openai import OpenAI
import tempfile
import asyncio
from typing import Callable, Optional
import logging

OPENAI_API_KEY = settings.OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)
logger = logging.getLogger(__name__)

def _transcribe_sync(audio_bytes: bytes, model: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        tmp.flush()
        with open(tmp.name, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=model,
                file=audio_file
            )
    return transcript.text

async def transcribe_with_gpt4o(
    audio_bytes: bytes,
    callback: Optional[Callable[[str], None]] = None,
    model: str = "gpt-4o-transcribe"
) -> str:
    """
    OpenAI公式ライブラリで音声データを文字起こしする
    :param audio_bytes: 音声データ（WAV/MP3/FLACなどOpenAI対応形式）
    :param callback: 結果を受け取るコールバック関数（省略可）
    :param model: 使用するモデル名（デフォルト: gpt-4o-transcribe）
    :return: 文字起こしテキスト
    """
    text = await asyncio.to_thread(_transcribe_sync, audio_bytes, model)
    logger.info(f"Transcription: {text}")
    if callback:
        callback(text)

    return text 