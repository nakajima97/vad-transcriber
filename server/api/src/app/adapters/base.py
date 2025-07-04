from abc import ABC, abstractmethod
from typing import Optional, Union, Callable, Awaitable


class BaseAdapter(ABC):
    """
    すべてのアダプターの基底クラス
    外部サービスとの通信を抽象化する
    """

    def __init__(self, **kwargs):
        """
        アダプターの初期化
        :param kwargs: アダプター固有の設定パラメータ
        """
        self.config = kwargs

    @abstractmethod
    async def health_check(self) -> bool:
        """
        外部サービスの健康状態をチェック
        :return: サービスが正常に動作している場合 True
        """
        pass


class TranscriptionAdapter(BaseAdapter):
    """
    音声文字起こしサービスの抽象化
    """

    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        model: str = "default",
        language: str = "ja",
        callback: Optional[
            Union[Callable[[str], None], Callable[[str], Awaitable[None]]]
        ] = None,
    ) -> str:
        """
        音声データを文字起こし
        :param audio_bytes: 音声データ（バイト列）
        :param model: 使用するモデル名
        :param language: 言語コード
        :param callback: 結果を受け取るコールバック関数
        :return: 文字起こし結果
        """
        pass

    @abstractmethod
    def get_supported_models(self) -> list[str]:
        """
        サポートされているモデルの一覧を取得
        :return: モデル名のリスト
        """
        pass


class VADAdapter(BaseAdapter):
    """
    音声検出サービスの抽象化
    """

    @abstractmethod
    def predict(
        self,
        audio_bytes: bytes,
        sample_rate: int = 16000,
        threshold: float = 0.5,
    ) -> tuple[bool, float]:
        """
        音声検出を実行
        :param audio_bytes: 音声データ（PCMバイト列）
        :param sample_rate: サンプリングレート
        :param threshold: 音声判定の閾値
        :return: (is_speech, speech_probability)
        """
        pass

    @abstractmethod
    def get_optimal_chunk_size(self) -> int:
        """
        最適なチャンクサイズを取得
        :return: チャンクサイズ（バイト）
        """
        pass
