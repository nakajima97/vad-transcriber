# FastAPI レイヤードアーキテクチャ 構成図

## アーキテクチャフロー図

```mermaid
graph TD
    A["HTTP Request"] --> B["API Layer<br/>(endpoints)"]
    B --> C["Service Layer<br/>(business logic)"]
    C --> D["Repository Layer<br/>(database)"]
    C --> E["Adapter Layer<br/>(external APIs)"]
    D --> F["Database"]
    E --> G["External Services<br/>(OpenAI, Slack, etc.)"]
    
    H["models/"] --> D
    I["schemas/"] --> B
    J["core/"] --> B
    J --> C
    K["utils/"] --> C
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#fff3e0
    style D fill:#e8f5e8
    style E fill:#ffebee
    style F fill:#f1f8e9
    style G fill:#fce4ec
```

## ディレクトリ構造図

```mermaid
graph TD
    Root["api/"] --> Src["src/"]
    Root --> Tests["tests/"]
    Root --> Config["pyproject.toml"]
    
    Src --> App["app/"]
    Src --> Migrations["migrations/"]
    
    App --> API["api/<br/>・deps.py<br/>・v1/endpoints/"]
    App --> Core["core/<br/>・config.py<br/>・security.py<br/>・database.py"]
    App --> Models["models/<br/>・base.py<br/>・user.py<br/>・item.py"]
    App --> Schemas["schemas/<br/>・user.py<br/>・item.py<br/>・auth.py"]
    App --> Repos["repositories/<br/>・base.py<br/>・user_repository.py<br/>・item_repository.py"]
    App --> Adapters["adapters/<br/>・base.py<br/>・openai_adapter.py<br/>・slack_adapter.py"]
    App --> Services["services/<br/>・user_service.py<br/>・item_service.py<br/>・ai_service.py"]
    App --> Utils["utils/<br/>・helpers.py<br/>・exceptions.py"]
    App --> Main["main.py"]
    
    Tests --> TestAPI["test_api/"]
    Tests --> TestServices["test_services/"]
    Tests --> TestRepos["test_repositories/"]
    Tests --> TestAdapters["test_adapters/"]
    
    style API fill:#f3e5f5
    style Services fill:#fff3e0
    style Repos fill:#e8f5e8
    style Adapters fill:#ffebee
    style Core fill:#e3f2fd
    style Models fill:#f1f8e9
    style Schemas fill:#fce4ec
```

## 依存関係の方向

```mermaid
graph LR
    API["API Layer"] --> Services["Service Layer"]
    Services --> Repos["Repository Layer"]
    Services --> Adapters["Adapter Layer"]
    
    Services --> Utils["Utils"]
    API --> Schemas["Schemas"]
    Repos --> Models["Models"]
    
    Services --> Core["Core"]
    API --> Core
    
    style API fill:#f3e5f5
    style Services fill:#fff3e0
    style Repos fill:#e8f5e8
    style Adapters fill:#ffebee
    style Core fill:#e3f2fd
    style Models fill:#f1f8e9
    style Schemas fill:#fce4ec
    style Utils fill:#f9f9f9
```

## 各層の責任範囲

| 層 | 責任 | 依存先 | 注意点 |
|---|-----|-------|-------|
| **API Layer** | HTTPリクエスト処理 | Service Layer, Schemas, Core | ビジネスロジックを含まない |
| **Service Layer** | ビジネスロジック実装 | Repository Layer, Adapter Layer, Utils, Core | 複数のリポジトリ・アダプターを協調 |
| **Repository Layer** | データベースアクセス | Models, Core | 外部APIアクセスは含まない |
| **Adapter Layer** | 外部システム通信 | Core | データベースアクセスは含まない |
| **Core** | 設定・共通機能 | なし | 他の層から参照される基盤 |
| **Models** | データベーススキーマ | なし | SQLAlchemyモデル定義 |
| **Schemas** | API入出力定義 | なし | Pydanticモデル定義 |
| **Utils** | ユーティリティ | なし | 汎用ヘルパー関数 |

## 実装時のポイント

### 1. 依存性注入パターン
- FastAPIの`Depends()`を活用
- テスト時のモック化を容易にする
- 各層間の疎結合を保つ

### 2. 単一責任の原則
- 各ファイル・クラスは一つの責任のみ持つ
- 機能追加時も既存コードへの影響を最小化

### 3. インターフェース分離
- アダプターには抽象基底クラスを使用
- 実装の詳細を隠蔽し、テスタビリティを向上

### 4. 例外処理
- 各層で適切な例外処理を実装
- カスタム例外クラスでドメイン固有のエラーを表現 