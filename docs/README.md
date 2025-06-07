# VAD Transcriber Documentation

このディレクトリには、VAD Transcriber プロジェクトのドキュメントが含まれています。

## ドキュメント構成

### フロントエンド (Next.js)
- [ディレクトリ構造](./frontend/directory-structure.md) - フロントエンドのディレクトリ構造と各ディレクトリの役割
- [コーディングガイドライン](./frontend/cording-guidline.md) - TypeScript/React のコーディングルール

### サーバー (FastAPI)
- [サーバー概要](./server/README.md) - サーバー関連ドキュメントの案内
- [ディレクトリ構造](./server/directory-structure.md) - レイヤードアーキテクチャの詳細構造
- [アーキテクチャ図](./server/architecture-diagram.md) - 視覚的なアーキテクチャ図とフロー

## 読み始める順番

### 新規参加者向け
1. **フロントエンド**: `frontend/directory-structure.md` → `frontend/cording-guidline.md`
2. **サーバー**: `server/README.md` → `server/directory-structure.md` → `server/architecture-diagram.md`

### 開発者向け
- 実装に迷った時は各ディレクトリ構造ドキュメントを参照
- 新機能追加時はアーキテクチャ図を確認して適切な層に実装

## 貢献について

ドキュメントの改善や追加については、プルリクエストをお送りください。新機能を追加した際は、関連するドキュメントの更新も忘れずに行ってください。 