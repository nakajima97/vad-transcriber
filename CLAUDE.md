# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

VAD Transcriber は、音声アクティビティ検出（VAD）を使用したリアルタイム音声文字起こしアプリケーションです。Next.js フロントエンドと FastAPI バックエンドで構成され、WebSocket 接続を通じて音声ストリームを処理し、音声検出には Silero VAD、文字起こしには OpenAI GPT-4o を使用します。

## 開発コマンド

### セットアップ
```bash
# フロントエンド依存関係
cd frontend && yarn install

# バックエンド依存関係
cd server/api && uv sync
```

### 開発サーバー起動
```bash
# バックエンドサービス起動（データベース含む）
make server-up

# フロントエンド開発サーバー起動
make front-up
```

### テストとリンティング
```bash
# フロントエンド
make front-test    # Vitest テスト実行
make front-lint    # Biome リンター実行
make front-tsc     # TypeScript 型チェック

# バックエンド
make server-test      # pytest テスト実行
make server-lint      # ruff リンター実行
make server-lint-fix  # ruff 自動修正

# 個別テスト実行
cd frontend && yarn test <test-file>  # 特定のフロントエンドテスト実行
cd server && docker compose exec api uv run pytest <test-file>  # 特定のバックエンドテスト実行
```

### ビルド
```bash
# フロントエンドビルド
cd frontend && yarn build

# Storybook ビルド
cd frontend && yarn build-storybook
```

## アーキテクチャ概要

### 高レベル構造
- **フロントエンド**: Next.js 15 + TypeScript でリアルタイム音声録音機能
- **バックエンド**: FastAPI + WebSocket によるリアルタイム通信
- **音声処理**: Silero VAD による音声検出、OpenAI GPT-4o による文字起こし
- **データベース**: PostgreSQL（将来のセッション保存用）

### 主要コンポーネント

**フロントエンド (`frontend/src/`):**
- `components/AudioRecorder.tsx`: WebSocket 統合を含むメイン音声録音コンポーネント
- `lib/useAudioRecorder.ts`: 音声録音ロジック用カスタムフック
- `lib/useAutoScroll.ts`: 文字起こし結果の自動スクロール機能
- `lib/types.ts`: 文字起こしモデルと結果の型定義

**バックエンド (`server/api/src/`):**
- `main.py`: WebSocket エンドポイントを含む FastAPI アプリケーション設定
- `app/websocket/handlers.py`: WebSocket 接続管理と音声処理
- `app/services/vad_chunk.py`: VAD 処理ロジック
- `app/utils/openai_transcribe.py`: OpenAI API 統合

### データフロー
1. **音声キャプチャ**: ブラウザの MediaRecorder API が音声を取得
2. **WebSocket ストリーミング**: リアルタイム音声データを FastAPI バックエンドに送信
3. **VAD 処理**: Silero VAD が音声セグメントを検出
4. **セグメント結合**: 短いセグメントを賢く結合して文字起こし品質を向上
5. **文字起こし**: 音声セグメントを OpenAI GPT-4o API に送信
6. **リアルタイム結果**: 文字起こし結果をフロントエンドにストリーミング

### WebSocket 通信
- **音声データ**: バイナリ PCM 音声データ（16kHz、16ビット、モノラル）
- **制御メッセージ**: モデル選択と設定用の JSON メッセージ
- **結果**: 信頼度スコアとタイムスタンプ付きの文字起こし結果

### 音声処理パイプライン
1. **入力フォーマット**: 16kHz、16ビット、モノラル PCM
2. **VAD 処理**: 音声検出用の 512 サンプルフレーム
3. **セグメント抽出**: 設定可能な無音許容時間での音声セグメント
4. **インテリジェント結合**: 短いセグメント（<0.8秒）を後続セグメントと結合
5. **文字起こし**: 結合されたセグメントを選択されたモデルで処理

## 主要機能

### モデル選択
- 複数の文字起こしモデルが利用可能（GPT-4o バリアント）
- 接続確立前のモデル選択
- 各モデルのコスト表示

### セグメント管理
- API 呼び出しを削減するためのインテリジェントセグメント結合
- 設定可能な無音許容時間（デフォルト 1.5 秒）
- 音声セグメントの自動ファイル保存

### セッション管理
- クライアント毎の音声セグメントディレクトリ
- タイムスタンプ付きセッション組織
- 切断時の自動クリーンアップ

## バックエンドアーキテクチャ注意点

バックエンドはレイヤードアーキテクチャパターンに従います（`.cursorrules` に基づく）:
- **API Layer**: WebSocket ハンドラーと REST エンドポイント
- **Service Layer**: ビジネスロジックと処理（`app/services/`）
- **Repository Layer**: データアクセス（`app/repositories/`）
- **Adapter Layer**: 外部 API 統合（`app/adapters/`）

主要原則:
- 外部依存関係はアダプターパターンで抽象化
- `api/deps.py` での依存性注入関数
- レイヤー違反を避ける - 各レイヤーは特定の責任を持つ
- ドメイン駆動設計（DDD）の実装なし（個人開発には複雑すぎる）
- すべての外部依存関係はアダプターパターンで抽象化必須
- テスト可能性を考慮した設計（モック可能な依存関係）

## 環境設定

### バックエンド環境変数
```bash
VAD_SILENCE_TOLERANCE=1.5  # 無音許容時間（秒）
OPENAI_API_KEY=your_api_key_here
```

### フロントエンド設定
- WebSocket URL: `ws://localhost:8000/ws`（開発環境）
- 音声フォーマット: 16kHz、16ビット、モノラル PCM
- 文字起こし結果の自動スクロール有効

## 開発ガイドライン

### バックエンド開発
- レイヤードアーキテクチャを厳格に遵守 - レイヤー違反禁止
- 外部 API（OpenAI など）は `app/adapters/` でアダプターパターン使用必須
- データベース操作は `app/repositories/` のみ
- ビジネスロジックは `app/services/` のみ
- すべての依存性注入は `api/deps.py` で行う
- 実装ガイダンスは `docs/directory-structure.md` を参照

### 新機能実装
1. 適切なレイヤー配置のため `docs/directory-structure.md` を確認
2. 適切なレイヤー（API/Service/Repository/Adapter）に実装
3. `api/deps.py` に依存性注入を追加
4. レイヤー別テストを作成
5. 関連ドキュメントを更新