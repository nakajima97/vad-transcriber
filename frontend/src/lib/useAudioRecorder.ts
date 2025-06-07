import { useCallback, useEffect, useRef, useState } from 'react';

interface AudioRecorderOptions {
  websocketUrl?: string;
  sampleRate?: number;
  channels?: number;
  bufferSize?: number;
}

interface AudioRecorderState {
  isRecording: boolean;
  isConnected: boolean;
  error: string | null;
  audioLevel: number;
}

interface AudioRecorderActions {
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  connect: () => void;
  disconnect: () => void;
}

export const useAudioRecorder = (
  options: AudioRecorderOptions = {}
): AudioRecorderState & AudioRecorderActions => {
  const {
    websocketUrl = 'ws://localhost:8000/ws',
    sampleRate = 16000,
    channels = 1,
    bufferSize = 4096
  } = options;

  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);

  const websocketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // WebSocket接続
  const connect = useCallback(() => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      websocketRef.current = new WebSocket(websocketUrl);
      
      websocketRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
      };

      websocketRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
      };

      websocketRef.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection failed');
        setIsConnected(false);
      };

      websocketRef.current.onmessage = (event) => {
        // サーバーからのメッセージを処理
        try {
          const data = JSON.parse(event.data);
          console.log('Received message:', data);
          
          // メッセージタイプに応じて処理
          switch (data.type) {
            case 'connection_established':
              console.log('WebSocket connection established:', data.message);
              break;
            case 'audio_received':
              console.log(`Audio data received: ${data.data_size} bytes (packet #${data.packet_count})`);
              break;
            case 'statistics':
              console.log(`Statistics: ${data.total_packets} total packets`);
              break;
            case 'error':
              console.error('Server error:', data.message);
              setError(data.message);
              break;
            default:
              console.log('Unknown message type:', data.type);
          }
        } catch (err) {
          console.error('Failed to parse message:', err);
        }
      };
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
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

  // 音声データをWebSocketで送信
  const sendAudioData = useCallback((audioData: ArrayBuffer) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(audioData);
    }
  }, []);

  // 音声レベルの分析
  const analyzeAudioLevel = useCallback(() => {
    if (!analyserRef.current) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyserRef.current.getByteFrequencyData(dataArray);

    // 音声レベルを計算（RMS）
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
      sum += dataArray[i] * dataArray[i];
    }
    const rms = Math.sqrt(sum / bufferLength);
    const level = (rms / 255) * 100;
    
    setAudioLevel(level);
  }, []);

  // 録音開始
  const startRecording = useCallback(async () => {
    try {
      setError(null);

      // マイクアクセス許可を取得
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate,
          channelCount: channels,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      streamRef.current = stream;

      // AudioContextを設定
      audioContextRef.current = new AudioContext({ sampleRate });
      sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      
      analyserRef.current.fftSize = 2048;
      sourceRef.current.connect(analyserRef.current);

      // 音声レベル監視を開始
      intervalRef.current = setInterval(analyzeAudioLevel, 100);

      // MediaRecorderを設定
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });

      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          // Blobを ArrayBuffer に変換して送信
          event.data.arrayBuffer().then((arrayBuffer) => {
            sendAudioData(arrayBuffer);
          });
        }
      };

      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        setError('Recording failed');
      };

      // 定期的にデータを送信（100ms間隔）
      mediaRecorder.start(100);
      setIsRecording(true);

    } catch (err) {
      console.error('Failed to start recording:', err);
      setError(err instanceof Error ? err.message : 'Failed to access microphone');
    }
  }, [sampleRate, channels, sendAudioData, analyzeAudioLevel]);

  // 録音停止
  const stopRecording = useCallback(() => {
    setIsRecording(false);

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    sourceRef.current = null;
    analyserRef.current = null;
    mediaRecorderRef.current = null;
    setAudioLevel(0);
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
    audioLevel,
    startRecording,
    stopRecording,
    connect,
    disconnect,
  };
}; 