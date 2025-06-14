import torch
import numpy as np

# Silero VADモデルのロード（初回のみ）
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
