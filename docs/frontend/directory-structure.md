### 1.2 ディレクトリ構造
```
/
├── frontend/
│   ├── .storybook/            # Storybook 設定
│   ├── public/                # 静的ファイル
│   └── src/                   # Next.js アプリディレクトリ
│       ├── app/               # アプリのエントリポイント (Next.js App Router 使用)
│       │   └── (pages/)       # 各ページのファイル (app router の規約に従う)
│       ├── components/        # 再利用可能な UI コンポーネント (アプリ全体で共有)
│       │   ├── ComponentName/ # 例: Button, Input, Header など
│       │   │   ├── index.tsx
│       │   │   └── ComponentName.stories.tsx
│       │   └── ...
│       ├── features/          # 特定の機能に関するコンポーネント、ロジック、ページ
│       │   ├── featureName/   # 例: auth, productList, checkout など
│       │   │   ├── components/      # 機能固有の Presentational Components
│       │   │   │   ├── ComponentName/
│       │   │   │   │   ├── index.tsx
│       │   │   │   │   └── ComponentName.stories.tsx
│       │   │   │   └── ...
│       │   │   ├── containers/     # 機能固有の Container Components (ロジックと状態管理)
│       │   │   │   ├── ContainerName/
│       │   │   │   │   ├── index.tsx
│       │   │   │   │   └── useContainerHook.ts  # コンテナ用のカスタムフック
│       │   │   │   └── ...
│       │   │   ├── hooks/          # 機能固有のカスタムフック
│       │   │   ├── types/          # 機能固有の型定義
│       │   │   └── utils/          # 機能固有のユーティリティ関数
│       │   └── ...
│       ├── hooks/             # アプリ全体で共有するカスタム React フック
│       ├── lib/               # 共有ユーティリティとライブラリ
│       ├── services/          # API サービスレイヤー (API クライアント、データ変換など)
│       └── utils/             # アプリ全体で共有するユーティリティ関数
└── docs/                 # プロジェクトドキュメント
```
