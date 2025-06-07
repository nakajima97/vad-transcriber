import asyncio
import io
import logging
import tempfile
from typing import Optional

import numpy as np
import soundfile as sf
import subprocess
import os

logger = logging.getLogger(__name__)


class AudioProcessor:
    """音声データ処理クラス"""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.buffer = bytearray()

    async def process_webm_audio(self, audio_data: bytes) -> Optional[np.ndarray]:
        """WebM/Opus形式の音声データを処理してnumpy配列に変換"""
        try:
            # バッファに音声データを追加
            self.buffer.extend(audio_data)

            # 十分なデータが蓄積されたら処理を実行
            if len(self.buffer) > 1024:  # 最小サイズチェック
                # 一時ファイルに書き込んで処理
                audio_array = await self._convert_webm_to_numpy(bytes(self.buffer))

                # バッファをクリア（一部を保持して連続性を保つ）
                self.buffer = self.buffer[-512:]  # 少し重複させる

                return audio_array

        except Exception as e:
            logger.error(f"Error processing WebM audio: {e}")
            return None

    async def _convert_webm_to_numpy(self, audio_data: bytes) -> Optional[np.ndarray]:
        """WebM/Opusデータをnumpy配列に変換"""
        try:
            # 一時ファイルを作成
            with tempfile.NamedTemporaryFile(
                suffix=".webm", delete=False
            ) as temp_input:
                temp_input.write(audio_data)
                temp_input_path = temp_input.name

            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as temp_output:
                temp_output_path = temp_output.name

            try:
                # ffmpegを使用してWebM/OpusをWAVに変換
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    temp_input_path,
                    "-ar",
                    str(self.sample_rate),
                    "-ac",
                    "1",  # モノラル
                    "-f",
                    "wav",
                    temp_output_path,
                ]

                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    logger.error(f"FFmpeg error: {stderr.decode()}")
                    return None

                # WAVファイルを読み込み
                audio_array, _ = sf.read(temp_output_path)

                return audio_array.astype(np.float32)

            finally:
                # 一時ファイルを削除
                try:
                    os.unlink(temp_input_path)
                    os.unlink(temp_output_path)
                except:
                    pass

        except Exception as e:
            logger.error(f"Error converting WebM to numpy: {e}")
            return None

    def calculate_audio_level(self, audio_data: np.ndarray) -> float:
        """音声レベル（RMS）を計算"""
        try:
            if len(audio_data) == 0:
                return 0.0

            # RMS計算
            rms = np.sqrt(np.mean(audio_data**2))

            # 0-100のスケールに変換
            level = min(100.0, rms * 100 * 10)  # 適当なスケーリング

            return float(level)

        except Exception as e:
            logger.error(f"Error calculating audio level: {e}")
            return 0.0
