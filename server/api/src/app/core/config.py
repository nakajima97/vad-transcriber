class Settings:
    """アプリケーション設定クラス"""

    APP_NAME: str = "FastAPI Template"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "FastAPIのレイヤードアーキテクチャテンプレート"

    # データベース設定
    DATABASE_URL: str = "postgresql://user:password@postgres:5432/mydb"

    # その他の設定
    DEBUG: bool = True


settings = Settings()
