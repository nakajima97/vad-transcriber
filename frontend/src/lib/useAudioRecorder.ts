import { useCallback, useEffect, useRef, useState } from 'react';
import type {
  TranscriptionModel,
  TranscriptionResult,
  VADResult,
  WebSocketMessage,
  ModelSelectionMessage,
  ConnectionEstablishedMessage,
  ModelChangedMessage,
} from './types';

interface AudioRecorderOptions {
  websocketUrl?: string;
  onTranscriptionResult?: (result: TranscriptionResult) => void;
  onVADResult?: (result: VADResult) => void;
  onMessage?: (message: WebSocketMessage) => void;
  onModelChanged?: (model: TranscriptionModel) => void;
}

interface AudioRecorderState {
  isRecording: boolean;
  isConnected: boolean;
  error: string | null;
  audioLevel: number;
  currentModel: TranscriptionModel;
}

interface AudioRecorderActions {
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  connect: () => void;
  disconnect: () => void;
  selectModel: (model: TranscriptionModel) => void;
}

export const useAudioRecorder = (
  options: AudioRecorderOptions = {},
): AudioRecorderState & AudioRecorderActions => {
  const {
    websocketUrl = 'ws://localhost:8000/ws',
    onTranscriptionResult,
    onVADResult,
    onMessage,
    onModelChanged,
  } = options;

  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [currentModel, setCurrentModel] = useState<TranscriptionModel>('gpt-4o-transcribe');

  const websocketRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // AudioWorkletProcessorのコード（インライン）
  const workletProcessorCode = `
    class PCMWorkletProcessor extends AudioWorkletProcessor {
      constructor() {
        super();
        this._buffer = [];
      }
      process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (input && input[0]) {
          this._buffer.push(...input[0]);
          // 音量レベル（RMS）計算
          let sum = 0;
          for (let i = 0; i < input[0].length; i++) {
            sum += input[0][i] * input[0][i];
          }
          const rms = Math.sqrt(sum / input[0].length);
          this.port.postMessage({ type: 'level', rms });
          // 512サンプルごとに送信
          while (this._buffer.length >= 512) {
            const chunk = this._buffer.slice(0, 512);
            this._buffer = this._buffer.slice(512);
            // Float32→Int16変換
            const int16 = new Int16Array(512);
            for (let i = 0; i < 512; i++) {
              let s = Math.max(-1, Math.min(1, chunk[i]));
              int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }
            this.port.postMessage({ type: 'pcm', buffer: int16.buffer }, [int16.buffer]);
          }
        }
        return true;
      }
    }
    registerProcessor('pcm-worklet-processor', PCMWorkletProcessor);
  `;

  // WebSocketメッセージハンドラー
  const handleWebSocketMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log('[WebSocket] Received message:', data);

        // 上位コンポーネントにメッセージを通知
        if (onMessage) {
          onMessage(data);
        }

        switch (data.type) {
          case 'connection_established':
            console.log('[WebSocket] Connection established:', data.client_id);
            const establishedMessage = data as ConnectionEstablishedMessage;
            if (establishedMessage.current_model) {
              setCurrentModel(establishedMessage.current_model);
              console.log('[Model] Current model set to:', establishedMessage.current_model);
            }
            break;

          case 'transcription_result':
            console.log('[WebSocket] Transcription result:', data.text);
            if (onTranscriptionResult) {
              onTranscriptionResult({
                id: data.id,
                text: data.text,
                confidence: data.confidence,
                timestamp: data.timestamp,
                is_final: data.is_final,
                segment_id: data.segment_id,
              });
            }
            break;

          case 'vad_result':
            console.log('[WebSocket] VAD result:', data.is_speech);
            if (onVADResult) {
              onVADResult({
                is_speech: data.is_speech,
                confidence: data.confidence,
                timestamp: data.timestamp,
              });
            }
            break;

          case 'transcription_error':
            console.error('[WebSocket] Transcription error:', data.error);
            setError(`文字起こしエラー: ${data.error}`);
            break;

          case 'transcription_skipped':
            console.warn('[WebSocket] Transcription skipped:', data.reason);
            break;

          case 'audio_received':
            // 音声受信確認（デバッグ用、通常は非表示）
            // console.log('[WebSocket] Audio received:', data.data_size);
            break;

          case 'statistics':
            console.log('[WebSocket] Statistics:', data.total_packets);
            break;

          case 'model_changed':
            // 接続中のモデル変更は無効になったため、このケースは基本的に発生しない
            console.log('[WebSocket] Model changed (legacy):', data);
            break;

          case 'error':
            console.error('[WebSocket] Server error:', data.message);
            setError(`サーバーエラー: ${data.message}`);
            break;

          default:
            console.warn('[WebSocket] Unknown message type:', data.type);
        }
      } catch (err) {
        console.error('[WebSocket] Failed to parse message:', err);
      }
    },
    [onTranscriptionResult, onVADResult, onMessage],
  );

  // WebSocket接続
  const connect = useCallback(() => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) return;
    try {
      console.log('[WebSocket] Connecting to:', websocketUrl);
      websocketRef.current = new WebSocket(websocketUrl);
      websocketRef.current.binaryType = 'arraybuffer';

      websocketRef.current.onopen = () => {
        console.log('[WebSocket] Connected successfully');
        setIsConnected(true);
        setError(null);
        
        // 接続時にモデル情報を送信
        setTimeout(() => {
          if (websocketRef.current?.readyState === WebSocket.OPEN) {
            const message: ModelSelectionMessage = {
              type: 'model_selection',
              model: currentModel,
              timestamp: Date.now(),
            };
            
            websocketRef.current.send(JSON.stringify(message));
            console.log('[Model] Initial model selection sent:', message);
          }
        }, 100); // 少し遅延させて確実に送信
      };

      websocketRef.current.onmessage = handleWebSocketMessage;

      websocketRef.current.onclose = (event) => {
        console.log('[WebSocket] Connection closed:', event.code, event.reason);
        setIsConnected(false);
      };

      websocketRef.current.onerror = (event) => {
        console.error('[WebSocket] Connection error:', event);
        setError('WebSocket接続に失敗しました');
        setIsConnected(false);
      };
    } catch (err) {
      console.error('[WebSocket] Failed to create connection:', err);
      setError('WebSocket接続の作成に失敗しました');
    }
  }, [websocketUrl, handleWebSocketMessage, currentModel]);

  // WebSocket切断
  const disconnect = useCallback(() => {
    if (websocketRef.current) {
      console.log('[WebSocket] Disconnecting...');
      websocketRef.current.close();
      websocketRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // 録音開始
  const startRecording = useCallback(async () => {
    try {
      setError(null);
      if (!isConnected) connect();

      console.log('[Audio] Starting recording...');

      // マイクストリーム取得
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      // AudioContext生成
      const audioContext = new AudioContext({ sampleRate: 16000 });
      audioContextRef.current = audioContext;

      // AudioWorklet登録
      const blob = new Blob([workletProcessorCode], {
        type: 'application/javascript',
      });
      const url = URL.createObjectURL(blob);
      await audioContext.audioWorklet.addModule(url);
      URL.revokeObjectURL(url);

      // Workletノード作成
      const workletNode = new AudioWorkletNode(
        audioContext,
        'pcm-worklet-processor',
      );
      workletNodeRef.current = workletNode;

      // WorkletからPCMデータ受信→WebSocket送信
      workletNode.port.onmessage = (event) => {
        const data = event.data;
        if (data && data.type === 'level') {
          setAudioLevel(Math.min(100, data.rms * 100));
        } else if (data && data.type === 'pcm') {
          if (websocketRef.current?.readyState === WebSocket.OPEN) {
            websocketRef.current.send(data.buffer);
          }
        }
      };

      // マイク→Worklet接続
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(workletNode);
      workletNode.connect(audioContext.destination); // 無音出力

      setIsRecording(true);
      console.log('[Audio] Recording started');
    } catch (err) {
      console.error('[Audio] Failed to start recording:', err);
      setError('録音の開始に失敗しました');
    }
  }, [isConnected, connect]);

  // 録音停止
  const stopRecording = useCallback(() => {
    console.log('[Audio] Stopping recording...');
    setIsRecording(false);

    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect();
      workletNodeRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      for (const track of streamRef.current.getTracks()) {
        track.stop();
      }
      streamRef.current = null;
    }

    setAudioLevel(0);
    console.log('[Audio] Recording stopped');
  }, []);

  // モデル選択（接続前のみ）
  const selectModel = useCallback((model: TranscriptionModel) => {
    console.log('[Model] Selecting model:', model);
    
    if (isConnected) {
      console.warn('[Model] Cannot change model while connected');
      setError('接続中はモデルを変更できません。');
      return;
    }
    
    // 接続前なので、状態のみ更新
    setCurrentModel(model);
    console.log('[Model] Model set for next connection:', model);
  }, [isConnected]);

  // クリーンアップ
  useEffect(() => {
    return () => {
      stopRecording();
      disconnect();
    };
  }, [stopRecording, disconnect]);

  return {
    isRecording,
    isConnected,
    error,
    audioLevel,
    currentModel,
    startRecording,
    stopRecording,
    connect,
    disconnect,
    selectModel,
  };
};
