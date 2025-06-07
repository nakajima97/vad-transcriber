# VAD Transcriber

音声アクティビティ検出（Voice Activity Detection）を使用した音声転写アプリケーション

## 🚀 技術スタック

- **フロントエンド**: Next.js 15 + TypeScript
- **バックエンド**: FastAPI + Python 3.12
- **データベース**: PostgreSQL
- **開発ツール**: Docker, GitHub Actions

## 📖 ドキュメント

詳細なドキュメントは [`docs/`](./docs/) ディレクトリにあります：

- [📋 ドキュメント概要](./docs/README.md)
- [🎨 フロントエンド構成](./docs/frontend/)
- [🔌 サーバー構成](./docs/server/)

## ⚡ クイックスタート

### 前提条件

- Node.js 22.x
- Python 3.12.2
- Docker & Docker Compose

### セットアップ

```bash
# リポジトリのクローン
git clone <repository-url>
cd vad-transcriber

# フロントエンドのセットアップ
cd frontend
yarn install

# サーバーのセットアップ
cd ../server/api
curl -LsSf https://astral.sh/uv/install.sh | sh  # uv のインストール
uv sync

# データベースの起動
cd ..
docker-compose up -d
```

### 開発サーバーの起動

```bash
# フロントエンド (http://localhost:3000)
cd frontend
yarn dev

# バックエンド (http://localhost:8000)
cd server/api
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## 🧪 テスト

```bash
# フロントエンド
cd frontend
yarn test
yarn lint
yarn type-check

# サーバー
cd server/api
uv run pytest
uv run ruff check .
```

## 📦 ビルド

```bash
# フロントエンド
cd frontend
yarn build

# Storybook
yarn build-storybook
```

## 🤝 貢献

1. フォークしてブランチを作成
2. 機能追加・バグ修正
3. テストの追加・実行
4. プルリクエストの作成

詳細は [ドキュメント](./docs/) を参照してください。

## 📄 ライセンス

MIT License
