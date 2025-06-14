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

# フロントエンド依存インストール（手動）
cd frontend
yarn install

# サーバー依存インストール（手動）
cd ../server/api
curl -LsSf https://astral.sh/uv/install.sh | sh  # uv のインストール
uv sync

# データベース・サーバー起動
cd ../..
make server-up
```

### 開発サーバーの起動

```bash
# フロントエンド
make front-up

# バックエンド（API含むサーバー全体）
make server-up
```

## 🧪 テスト

```bash
# フロントエンド
make front-test
make front-lint
make front-tsc

# サーバー
make server-test
make server-lint
```

## 📦 ビルド

```bash
# フロントエンド（手動）
cd frontend
yarn build

# Storybook（手動）
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
