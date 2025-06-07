# FastAPI レイヤードアーキテクチャ ディレクトリ設計

## ディレクトリ構造

```
api/
├── src/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPIアプリケーションの起動点
│   │   │
│   │   ├── api/                         # APIルーター群
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                  # 依存性注入
│   │   │   └── v1/                      # バージョン管理
│   │   │       ├── __init__.py
│   │   │       ├── endpoints/           # エンドポイント定義
│   │   │       │   ├── __init__.py
│   │   │       │   ├── users.py
│   │   │       │   ├── items.py
│   │   │       │   └── auth.py
│   │   │       └── router.py            # v1のルーター統合
│   │   │
│   │   ├── core/                        # アプリケーションのコア設定
│   │   │   ├── __init__.py
│   │   │   ├── config.py                # 環境変数・設定管理
│   │   │   ├── security.py              # 認証・認可機能
│   │   │   └── database.py              # データベース接続設定
│   │   │
│   │   ├── models/                      # データベースモデル（SQLAlchemy）
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # ベースモデルクラス
│   │   │   ├── user.py                  # ユーザーモデル
│   │   │   └── item.py                  # アイテムモデル
│   │   │
│   │   ├── schemas/                     # Pydanticスキーマ（リクエスト・レスポンス）
│   │   │   ├── __init__.py
│   │   │   ├── user.py                  # ユーザー関連スキーマ
│   │   │   ├── item.py                  # アイテム関連スキーマ
│   │   │   └── auth.py                  # 認証関連スキーマ
│   │   │
│   │   ├── repositories/                # データアクセス層（データベース専用）
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # 基底リポジトリクラス
│   │   │   ├── user_repository.py       # ユーザーデータアクセス
│   │   │   └── item_repository.py       # アイテムデータアクセス
│   │   │
│   │   ├── adapters/                    # 外部システムとの通信アダプター
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # 基底アダプタークラス
│   │   │   ├── openai_adapter.py        # OpenAI API通信
│   │   │   ├── slack_adapter.py         # Slack API通信
│   │   │   ├── stripe_adapter.py        # Stripe決済API
│   │   │   └── email_adapter.py         # メール送信サービス
│   │   │
│   │   ├── services/                    # ビジネスロジック層
│   │   │   ├── __init__.py
│   │   │   ├── user_service.py          # ユーザー関連ビジネスロジック
│   │   │   ├── item_service.py          # アイテム関連ビジネスロジック
│   │   │   ├── ai_service.py            # AI機能のビジネスロジック
│   │   │   └── auth_service.py          # 認証関連ビジネスロジック
│   │   │
│   │   └── utils/                       # ユーティリティ・ヘルパー関数
│   │       ├── __init__.py
│   │       ├── helpers.py               # 汎用ヘルパー関数
│   │       └── exceptions.py            # カスタム例外クラス
│   │
│   └── migrations/                      # Alembicデータベースマイグレーション
│       ├── versions/
│       └── env.py
│
├── tests/                               # テストコード
│   ├── __init__.py
│   ├── conftest.py                      # テスト共通設定
│   ├── test_api/                        # APIエンドポイントテスト
│   ├── test_services/                   # サービス層テスト
│   ├── test_repositories/               # リポジトリ層テスト
│   └── test_adapters/                   # アダプター層テスト
│
├── pyproject.toml                       # プロジェクト設定・依存関係
├── uv.lock                              # 依存関係ロックファイル
├── alembic.ini                          # Alembic設定
├── Dockerfile                           # Dockerコンテナ設定
└── README.md                            # プロジェクト説明

```

## 各層の責任と役割

### 1. API層 (`api/`)
- **責任**: HTTPリクエストの受け取りとレスポンスの返却
- **含むもの**: ルーター、エンドポイント、依存性注入
- **特徴**: ビジネスロジックは含まず、サービス層に処理を委譲

### 2. サービス層 (`services/`)
- **責任**: ビジネスロジックの実装
- **含むもの**: アプリケーションのコアロジック、複数のリポジトリ・アダプターの協調
- **特徴**: トランザクション管理、複雑な業務処理の統合

### 3. リポジトリ層 (`repositories/`)
- **責任**: データベースとの通信専用
- **含むもの**: CRUD操作、クエリ実行
- **特徴**: データベース技術の詳細を隠蔽

### 4. アダプター層 (`adapters/`)
- **責任**: 外部システムとの通信
- **含むもの**: 外部API呼び出し、第三者サービス統合
- **特徴**: 外部依存の詳細を隠蔽、テスト時のモック化が容易

### 5. モデル層 (`models/`)
- **責任**: データベーススキーマの定義
- **含むもの**: SQLAlchemyモデル、テーブル定義
- **特徴**: データの永続化形式を定義

### 6. スキーマ層 (`schemas/`)
- **責任**: API入出力データの検証と型定義
- **含むもの**: Pydanticモデル、バリデーションルール
- **特徴**: リクエスト・レスポンスの型安全性を保証

## データの流れ

```
HTTP Request
    ↓
API Layer (endpoints)
    ↓
Service Layer (business logic)
    ↓
Repository Layer (database) + Adapter Layer (external APIs)
    ↓
Database / External Services
```

## 設計の利点

1. **関心の分離**: 各層が明確な責任を持つ
2. **テスタビリティ**: 各層を独立してテスト可能
3. **保守性**: 変更の影響範囲が限定される
4. **拡張性**: 新機能追加時の構造が明確
5. **外部依存の管理**: アダプター層で外部サービスの詳細を隠蔽

## 命名規則

- **ファイル名**: スネークケース (`user_service.py`)
- **クラス名**: パスカルケース (`UserService`)
- **関数名**: スネークケース (`get_user_by_id`)
- **定数**: 大文字スネークケース (`API_VERSION`)

## 使用例

```python
# エンドポイントでの使用例
@router.post("/users/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.create_user(user_data)

# サービス層での使用例
class UserService:
    def __init__(self, user_repo: UserRepository, email_adapter: EmailAdapter):
        self.user_repo = user_repo
        self.email_adapter = email_adapter
    
    async def create_user(self, user_data: UserCreate) -> User:
        user = await self.user_repo.create(user_data)
        await self.email_adapter.send_welcome_email(user.email)
        return user
``` 