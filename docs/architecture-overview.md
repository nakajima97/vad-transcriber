# VAD Transcriber システムアーキテクチャ概要

## 1. システム全体構成

### 1.1 高レベルアーキテクチャ

```mermaid
graph TB
    subgraph "クライアント（ブラウザ）"
        A[音声入力] --> B[WebRTC/MediaRecorder]
        B --> C[WebSocket Client]
        C --> D[React UI]
        D --> E[文字起こし結果表示]
    end
    
    subgraph "フロントエンド（Next.js）"
        F[Next.js App Router]
        G[TypeScript Components]
        H[WebSocket Handler]
        I[Audio Processing]
    end
    
    subgraph "バックエンド（FastAPI）"
        J[WebSocket Server] --> K[Audio Buffer Manager]
        K --> L[Silero VAD Processor]
        L --> M[Audio Segment Extractor]
        M --> N[GPT-4o API Client]
        N --> O[Result Formatter]
        O --> J
    end
    
    subgraph "外部サービス"
        P[OpenAI GPT-4o API]
    end
    
    C <--> H
    H <--> J
    N <--> P
    
    style A fill:#e1f5fe
    style E fill:#e8f5e8
    style L fill:#fff3e0
    style N fill:#f3e5f5
```

### 1.2 データフロー詳細

```mermaid
sequenceDiagram
    participant U as User/Browser
    participant F as Frontend
    participant W as WebSocket
    participant V as VAD Processor
    participant G as GPT-4o API
    participant D as Database
    
    U->>F: 録音開始
    F->>W: WebSocket接続確立
    
    loop リアルタイム音声ストリーミング
        U->>F: 音声データ（PCM）
        F->>W: 音声チャンク送信
        W->>V: VAD処理実行
        
        alt 発話区間検出
            V->>V: 音声セグメント抽出
            V->>G: 音声データ送信
            G->>V: 文字起こし結果返却
            V->>W: 結果送信
            W->>F: 結果配信
            F->>U: リアルタイム表示
        else 無音区間
            V->>W: VAD結果（無音）送信
        end
    end
    
    U->>F: 録音停止
    F->>W: 接続切断
```

## 2. コンポーネント詳細

### 2.1 フロントエンド構成

```mermaid
graph LR
    subgraph "Next.js Application"
        A[app/] --> B[page.tsx]
        A --> C[layout.tsx]
        
        D[components/] --> E[AudioRecorder]
        D --> F[TranscriptionDisplay]
        D --> G[StatusIndicator]
        D --> H[SettingsPanel]
        
        I[hooks/] --> J[useWebSocket]
        I --> K[useAudioRecorder]
        I --> L[useTranscription]
        
        M[utils/] --> N[audioUtils]
        M --> O[websocketUtils]
        M --> P[formatUtils]
        
        Q[types/] --> R[audio.types.ts]
        Q --> S[websocket.types.ts]
        Q --> T[transcription.types.ts]
    end
    
    style E fill:#e3f2fd
    style F fill:#e8f5e8
    style J fill:#fff3e0
```

### 2.2 バックエンド構成

```mermaid
graph LR
    subgraph "FastAPI Application"
        A[src/] --> B[main.py]
        A --> C[config/]
        
        D[api/] --> E[websocket/]
        D --> F[transcription/]
        D --> G[sessions/]
        
        H[core/] --> I[vad_processor.py]
        H --> J[gpt4o_client.py]
        H --> K[audio_manager.py]
        
        L[models/] --> M[session.py]
        L --> N[websocket.py]
        
        P[services/] --> Q[transcription_service.py]
        P --> R[vad_service.py]
        P --> S[websocket_service.py]
        
        T[utils/] --> U[audio_processing.py]
        T --> V[format_converter.py]
        T --> W[logger.py]
    end
    
    style I fill:#fff3e0
    style J fill:#f3e5f5
    style Q fill:#e8f5e8
```

## 3. 技術スタック詳細

### 3.1 フロントエンド技術

| 技術 | バージョン | 用途 |
|------|------------|------|
| Next.js | 15.x | React フレームワーク |
| TypeScript | 5.x | 型安全性確保 |
| React | 18.x | UI コンポーネント |
| WebSocket API | Native | リアルタイム通信 |
| MediaRecorder API | Native | 音声録音 |
| Tailwind CSS | 3.x | スタイリング |
| Zustand | 4.x | 状態管理 |

### 3.2 バックエンド技術

| 技術 | バージョン | 用途 |
|------|------------|------|
| FastAPI | 0.110.x | Web フレームワーク |
| Python | 3.12 | 実行環境 |
| Silero VAD | latest | 音声アクティビティ検出 |
| PyTorch | 2.x | VAD モデル実行 |
| OpenAI API | 1.x | GPT-4o 音声認識 |
| uvicorn | 0.28.x | ASGI サーバー |

### 3.3 インフラ技術

| 技術 | バージョン | 用途 |
|------|------------|------|
| Docker | 24.x | コンテナ化 |
| Docker Compose | 3.8 | オーケストレーション |
| GitHub Actions | - | CI/CD |
| Nginx | 1.25 | リバースプロキシ |

## 4. 音声処理パイプライン

### 4.1 音声データ変換フロー

```mermaid
graph TD
    A[Browser Audio Input] -->|MediaRecorder| B[WebM/PCM Data]
    B -->|WebSocket| C[Server Audio Buffer]
    C -->|Format Conversion| D[16kHz Mono PCM]
    D -->|VAD Processing| E[Silero VAD Analysis]
    
    E -->|Speech Detected| F[Audio Segment Extraction]
    E -->|Silence Detected| G[Discard Segment]
    
    F -->|Audio Encoding| H[Base64/WAV Format]
    H -->|API Request| I[GPT-4o Transcription]
    I -->|Response| J[Transcription Result]
    J -->|WebSocket| K[Frontend Display]
    
    style E fill:#fff3e0
    style I fill:#f3e5f5
    style K fill:#e8f5e8
```

### 4.2 VAD処理詳細

```mermaid
graph LR
    subgraph "VAD Processing Pipeline"
        A[Raw Audio] --> B[Preprocessing]
        B --> C[Feature Extraction]
        C --> D[Silero Model Inference]
        D --> E[Confidence Scoring]
        E --> F[Threshold Decision]
        
        F -->|Confidence > 0.5| G[Speech Segment]
        F -->|Confidence ≤ 0.5| H[Silence Segment]
        
        G --> I[Audio Buffer Accumulation]
        I -->|Buffer Full| J[Send to GPT-4o]
        H --> K[Discard Data]
    end
    
    style D fill:#fff3e0
    style G fill:#e8f5e8
    style J fill:#f3e5f5
```

## 5. WebSocket通信仕様

### 5.1 接続管理

```mermaid
stateDiagram-v2
    [*] --> Disconnected
    Disconnected --> Connecting : connect()
    Connecting --> Connected : onopen
    Connecting --> Error : onerror
    Connected --> Streaming : start_recording
    Streaming --> Connected : stop_recording
    Connected --> Disconnected : disconnect()
    Error --> Connecting : retry
    Error --> Disconnected : give_up
    
    state Connected {
        [*] --> Idle
        Idle --> Processing : audio_data
        Processing --> Idle : processing_complete
    }
```

### 5.2 メッセージタイプ

| メッセージタイプ | 方向 | 説明 |
|------------------|------|------|
| `audio_data` | Client → Server | 音声データチャンク |
| `transcription_result` | Server → Client | 文字起こし結果 |
| `vad_result` | Server → Client | VAD処理結果 |
| `error` | Server → Client | エラー通知 |
| `status` | Server → Client | システム状態 |
| `config` | Client → Server | 設定変更 |

## 6. エラーハンドリング戦略

### 6.1 エラー分類

```mermaid
graph TD
    A[Error Detected] --> B{Error Type}
    
    B -->|Network| C[Connection Error]
    B -->|Audio| D[Audio Processing Error]
    B -->|API| E[GPT-4o API Error]
    B -->|VAD| F[VAD Processing Error]
    B -->|System| G[System Error]
    
    C --> H[Retry Connection]
    D --> I[Reset Audio Pipeline]
    E --> J[Queue for Retry]
    F --> K[Fallback Processing]
    G --> L[Log & Alert]
    
    H --> M[Recovery Success?]
    I --> M
    J --> M
    K --> M
    L --> M
    
    M -->|Yes| N[Continue Operation]
    M -->|No| O[Graceful Degradation]
    
    style C fill:#ffebee
    style E fill:#fff3e0
    style O fill:#fce4ec
```

### 6.2 復旧メカニズム

| エラータイプ | 復旧手順 | タイムアウト |
|--------------|----------|--------------|
| WebSocket切断 | 自動再接続（指数バックオフ） | 30秒 |
| GPT-4o API エラー | リトライキューイング | 60秒 |
| VAD処理エラー | フォールバック処理 | 即座 |
| 音声入力エラー | デバイス再初期化 | 10秒 |
| システムエラー | ログ記録・アラート | - |

## 7. セキュリティ考慮事項

### 7.1 データ保護フロー

```mermaid
graph TD
    A[Audio Input] -->|Encryption| B[Encrypted Transport]
    B --> C[Server Processing]
    C -->|Temporary Storage| D[In-Memory Buffer]
    D --> E[VAD Processing]
    E --> F[GPT-4o API Call]
    F --> G[Transcription Result]
    G --> H[Response to Client]
    
    D -->|Auto Cleanup| I[Memory Clear]
    F -->|API Response| J[Audio Data Deletion]
    
    style B fill:#e3f2fd
    style I fill:#e8f5e8
    style J fill:#fff3e0
```

### 7.2 認証・認可

| レイヤー | 認証方式 | 認可レベル |
|----------|----------|------------|
| WebSocket | セッショントークン | ユーザーレベル |
| REST API | JWT トークン | ロールベース |
| GPT-4o API | API キー | サービスレベル |

## 8. 監視・ログ戦略

### 8.1 メトリクス収集

```mermaid
graph LR
    subgraph "Monitoring Stack"
        A[Application Metrics] --> D[Prometheus]
        B[System Metrics] --> D
        C[Custom Metrics] --> D
        
        D --> E[Grafana Dashboard]
        D --> F[AlertManager]
        
        G[Application Logs] --> H[Structured Logging]
        H --> I[Log Aggregation]
        I --> J[Log Analysis]
    end
    
    style D fill:#e3f2fd
    style E fill:#e8f5e8
    style H fill:#fff3e0
```

### 8.2 重要指標

| カテゴリ | 指標 | 閾値 |
|----------|------|------|
| パフォーマンス | WebSocket遅延 | < 50ms |
| パフォーマンス | VAD処理時間 | < 100ms |
| パフォーマンス | GPT-4o応答時間 | < 3s |
| 可用性 | システム稼働率 | > 99.5% |
| エラー | エラー率 | < 1% |
| リソース | メモリ使用率 | < 80% |
| リソース | CPU使用率 | < 70% |

## 9. デプロイメント戦略

### 9.1 コンテナ構成

```mermaid
graph TB
    subgraph "Production Environment"
        A[Load Balancer] --> B[Frontend Container]
        A --> C[Backend Container]
        
        F[Nginx Container] --> B
        F --> C
        
        G[Monitoring Container] --> C
    end
    
    subgraph "External Services"
        H[OpenAI API]
        I[CDN]
    end
    
    C --> H
    B --> I
    
    style A fill:#e3f2fd
    style C fill:#fff3e0
    style G fill:#e8f5e8
```

### 9.2 CI/CD パイプライン

| ステージ | 処理内容 | 条件 |
|----------|----------|------|
| Build | Docker イメージビルド | Push to main |
| Test | 単体・結合テスト実行 | 全ブランチ |
| Security | セキュリティスキャン | Pull Request |
| Deploy Staging | ステージング環境デプロイ | main ブランチ |
| Deploy Production | 本番環境デプロイ | タグプッシュ |

この包括的なアーキテクチャ概要により、開発チーム全体がシステムの全体像を理解し、効率的な開発を進めることができます。 