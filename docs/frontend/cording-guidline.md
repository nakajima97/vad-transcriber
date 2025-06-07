- TypeScriptの型定義を厳格に行う
- Biomeを使用したコード品質の維持
- コンポーネント設計はPresentational/Containerパターンに従う
- コメントは日本語で書く
- 型定義は`type`キーワードを使用する
- 関数宣言は`function`キーワードを使わず、`const`とアロー関数を使用する
  ```typescript
  // 推奨
  export const MyComponent = () => {
    // 実装
  };

  // 非推奨
  export function MyComponent() {
    // 実装
  }
  ```
- テストコードの採用
  - Presentationalコンポーネントのテスト
    - Storybookのストーリーの作成
  - Containerコンポーネントのテスト
    - vitestによる単体テスト