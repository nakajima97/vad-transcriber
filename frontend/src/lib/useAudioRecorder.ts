import { useCallback, useEffect, useRef, useState } from 'react';

interface AudioRecorderOptions {
  websocketUrl?: string;
}

interface AudioRecorderState {
  isRecording: boolean;
  isConnected: boolean;
  error: string | null;
}

interface AudioRecorderActions {
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  connect: () => void;
  disconnect: () => void;
}

export const useAudioRecorder = (
  options: AudioRecorderOptions = {},
): AudioRecorderState & AudioRecorderActions => {
  const { websocketUrl = 'ws://localhost:8000/ws' } = options;

  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
            this.port.postMessage(int16.buffer, [int16.buffer]);
          }
        }
        return true;
      }
    }
    registerProcessor('pcm-worklet-processor', PCMWorkletProcessor);
  `;

  // WebSocket接続
  const connect = useCallback(() => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) return;
    try {
      websocketRef.current = new WebSocket(websocketUrl);
      websocketRef.current.binaryType = 'arraybuffer';
      websocketRef.current.onopen = () => {
        setIsConnected(true);
        setError(null);
      };
      websocketRef.current.onclose = () => {
        setIsConnected(false);
      };
      websocketRef.current.onerror = (event) => {
        setError('WebSocket connection failed');
        setIsConnected(false);
      };
    } catch (err) {
      setError('Failed to create WebSocket connection');
    }
  }, [websocketUrl]);

  // WebSocket切断
  const disconnect = useCallback(() => {
    if (websocketRef.current) {
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
        if (websocketRef.current?.readyState === WebSocket.OPEN) {
          websocketRef.current.send(event.data);
        }
      };
      // マイク→Worklet接続
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(workletNode);
      workletNode.connect(audioContext.destination); // 無音出力
      setIsRecording(true);
    } catch (err) {
      setError('Failed to start recording');
    }
  }, [isConnected, connect]);

  // 録音停止
  const stopRecording = useCallback(() => {
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
  }, []);

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
    startRecording,
    stopRecording,
    connect,
    disconnect,
  };
};
