'use client';

import { useAudioRecorder } from '@/lib/useAudioRecorder';
import { AlertCircle, Mic, Square, Volume2, Wifi, WifiOff } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Badge } from './shadcn/ui/badge';
import { Button } from './shadcn/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from './shadcn/ui/card';
import { Progress } from './shadcn/ui/progress';

type TranscriptionResult = {
  id: string;
  text: string;
  confidence: number;
  timestamp: number;
  is_final: boolean;
  segment_id: number;
};

type VADResult = {
  is_speech: boolean;
  confidence: number;
  timestamp: number;
};

interface AudioRecorderProps {
  websocketUrl?: string;
  onTranscriptionResult?: (result: TranscriptionResult) => void;
  onVADResult?: (result: VADResult) => void;
}

export function AudioRecorder({
  websocketUrl = 'ws://localhost:8000/ws',
  onTranscriptionResult,
  onVADResult,
}: AudioRecorderProps) {
  const {
    isRecording,
    isConnected,
    error,
    audioLevel,
    startRecording,
    stopRecording,
    connect,
    disconnect,
  } = useAudioRecorder({ 
    websocketUrl,
    onTranscriptionResult,
    onVADResult,
  });

  const [sessionTime, setSessionTime] = useState(0);

  // セッション時間のカウント
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;

    if (isRecording) {
      interval = setInterval(() => {
        setSessionTime((prev) => prev + 1);
      }, 1000);
    } else {
      setSessionTime(0);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRecording]);

  const handleStartRecording = async () => {
    if (!isConnected) {
      connect();
      // 接続を待ってから録音開始
      setTimeout(() => {
        startRecording();
      }, 1000);
    } else {
      await startRecording();
    }
  };

  const handleStopRecording = () => {
    stopRecording();
    disconnect();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Card className="bg-white dark:bg-slate-800 border-0 shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Volume2 className="w-5 h-5 text-blue-600" />
          録音制御
        </CardTitle>
        <CardDescription>
          音声の録音とWebSocketでのリアルタイム送信
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 接続ステータス */}
        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
          <div className="flex items-center gap-2">
            <Badge
              variant={isConnected ? 'default' : 'secondary'}
              className="flex items-center gap-1"
            >
              {isConnected ? (
                <Wifi className="w-3 h-3" />
              ) : (
                <WifiOff className="w-3 h-3" />
              )}
              {isConnected ? '接続中' : '切断'}
            </Badge>
            <span className="text-sm text-slate-600 dark:text-slate-400">
              WebSocket: {websocketUrl}
            </span>
          </div>
          {!isConnected && !isRecording && (
            <Button
              variant="outline"
              size="sm"
              onClick={connect}
              className="text-xs"
            >
              手動接続
            </Button>
          )}
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded-lg">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* 録音ボタンとステータス */}
        <div className="flex items-center justify-center space-x-4">
          <Button
            size="lg"
            onClick={isRecording ? handleStopRecording : handleStartRecording}
            className={`
              w-32 h-32 rounded-full transition-all duration-300 
              ${
                isRecording
                  ? 'bg-red-500 hover:bg-red-600 animate-pulse shadow-lg shadow-red-200'
                  : 'bg-blue-500 hover:bg-blue-600 shadow-lg shadow-blue-200'
              }
            `}
            disabled={!isConnected && isRecording}
          >
            {isRecording ? (
              <Square className="w-8 h-8 text-white" />
            ) : (
              <Mic className="w-8 h-8 text-white" />
            )}
          </Button>
        </div>

        <div className="text-center space-y-2">
          <div className="text-xl font-semibold text-slate-900 dark:text-white">
            {isRecording ? '録音中...' : '待機中'}
          </div>
          {isRecording && (
            <div className="text-sm text-slate-600 dark:text-slate-400">
              録音時間: {formatTime(sessionTime)}
            </div>
          )}
        </div>

        {/* 音声レベルメーター */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-slate-600 dark:text-slate-400">
            <span>音声レベル</span>
            <span>{Math.round(audioLevel)}%</span>
          </div>
          <Progress value={audioLevel} className="w-full h-2" />
        </div>

        {/* 録音設定 */}
        <div className="grid grid-cols-2 gap-4 p-3 bg-slate-50 dark:bg-slate-700 rounded-lg text-sm">
          <div>
            <span className="text-slate-600 dark:text-slate-400">
              サンプルレート:
            </span>
            <span className="ml-2 font-medium">16kHz</span>
          </div>
          <div>
            <span className="text-slate-600 dark:text-slate-400">
              チャンネル:
            </span>
            <span className="ml-2 font-medium">モノラル</span>
          </div>
          <div>
            <span className="text-slate-600 dark:text-slate-400">
              フォーマット:
            </span>
            <span className="ml-2 font-medium">PCM 16bit</span>
          </div>
          <div>
            <span className="text-slate-600 dark:text-slate-400">
              送信間隔:
            </span>
            <span className="ml-2 font-medium">32ms</span>
          </div>
        </div>

        {/* 録音の説明 */}
        <div className="text-xs text-slate-500 dark:text-slate-400 space-y-1">
          <p>• マイクへのアクセス許可が必要です</p>
          <p>• 音声データはリアルタイムでWebSocketサーバーに送信されます</p>
          <p>• ノイズ除去と自動ゲイン制御が有効です</p>
          <p>• VADによる音声区間検出で効率的な文字起こしを実行</p>
        </div>
      </CardContent>
    </Card>
  );
}
