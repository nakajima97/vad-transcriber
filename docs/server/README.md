# FastAPI テンプレート ドキュメント

このディレクトリには、FastAPIプロジェクトの理解に必要なすべてのドキュメントが含まれています。

## ドキュメント一覧

### 🏗️ アーキテクチャ設計
- **[directory-structure.md](./directory-structure.md)** - 詳細なディレクトリ構造と各層の責任
- **[architecture-diagram.md](./architecture-diagram.md)** - 視覚的なアーキテクチャ図とフロー

## 📖 読み始める順番

1. **新規参加者**: `directory-structure.md` → `architecture-diagram.md`

## 🚀 クイックスタート

```bash
# 開発環境の起動
docker-compose up -d

# データベースマイグレーション
docker-compose exec api alembic upgrade head

# テスト実行
docker-compose exec api pytest
```

## 💡 ヒント

- 実装に迷った時は `directory-structure.md` の各層の責任を確認
- 新機能追加時は `architecture-diagram.md` の依存関係を参考に
- 外部API統合時は `directory-structure.md` のアダプターパターンを活用

## 📝 ドキュメント更新

新機能を追加した際は、関連するドキュメントの更新も忘れずに行ってください。特に：
- 新しいサービス層やアダプター: `directory-structure.md`
- アーキテクチャに影響する変更: `architecture-diagram.md` 