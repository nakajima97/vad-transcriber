// 音声認識モデルの定義
export type TranscriptionModel = 'whisper-1' | 'gpt-4o-transcribe' | 'gpt-4o-mini-transcribe';

// 利用可能なモデル情報
export interface ModelInfo {
  id: TranscriptionModel;
  name: string;
  description: string;
  features: string[];
  cost: 'low' | 'medium' | 'high';
}

// 利用可能なモデル一覧
export const AVAILABLE_MODELS: ModelInfo[] = [
  {
    id: 'gpt-4o-transcribe',
    name: 'GPT-4o Transcribe',
    description: '最新世代の高精度 Speech-to-Text モデル',
    features: ['高精度', 'ノイズ耐性', 'リアルタイム対応'],
    cost: 'high',
  },
  {
    id: 'gpt-4o-mini-transcribe',
    name: 'GPT-4o Mini',
    description: 'GPT-4o Transcribe の軽量版',
    features: ['高速処理', '低コスト', '軽量'],
    cost: 'low',
  },
  {
    id: 'whisper-1',
    name: 'Whisper-1',
    description: '多言語対応の汎用音声認識モデル',
    features: ['多言語対応', '汎用性', 'バッチ処理'],
    cost: 'medium',
  },
];

// WebSocketメッセージタイプ
export type WebSocketMessageType = 
  | 'model_selection'
  | 'connection_established'
  | 'transcription_result'
  | 'vad_result'
  | 'transcription_error'
  | 'transcription_skipped'
  | 'audio_received'
  | 'statistics'
  | 'error'
  | 'segment_merge_error';

// WebSocketメッセージの基底型
export interface BaseWebSocketMessage {
  type: WebSocketMessageType;
  timestamp: number;
}

// クライアント → サーバー
export interface ModelSelectionMessage extends BaseWebSocketMessage {
  type: 'model_selection';
  model: TranscriptionModel;
}

// サーバー → クライアント
export interface ConnectionEstablishedMessage extends BaseWebSocketMessage {
  type: 'connection_established';
  client_id: string;
  message: string;
  model: TranscriptionModel;
}

export interface TranscriptionResultMessage extends BaseWebSocketMessage {
  type: 'transcription_result';
  id: string;
  text: string;
  confidence: number;
  is_final: boolean;
  segment_id: number;
  model_used: TranscriptionModel;
}

export interface VADResultMessage extends BaseWebSocketMessage {
  type: 'vad_result';
  is_speech: boolean;
  confidence: number;
}

export interface TranscriptionErrorMessage extends BaseWebSocketMessage {
  type: 'transcription_error';
  segment_id: number;
  error: string;
  model_used: TranscriptionModel;
}



export interface ErrorMessage extends BaseWebSocketMessage {
  type: 'error';
  message: string;
}

// Union型でメッセージタイプを統合
export type ClientMessage = ModelSelectionMessage;

export type ServerMessage = 
  | ConnectionEstablishedMessage
  | TranscriptionResultMessage
  | VADResultMessage
  | TranscriptionErrorMessage
  | ErrorMessage;

export type WebSocketMessage = ClientMessage | ServerMessage;

// レガシー型（既存コードとの互換性のため）
export interface TranscriptionResult {
  id: string;
  text: string;
  confidence: number;
  timestamp: number;
  is_final: boolean;
  segment_id: number;
  model_used?: TranscriptionModel;
}

export interface VADResult {
  is_speech: boolean;
  confidence: number;
  timestamp: number;
} 