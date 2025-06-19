'use client';

import { useAudioRecorder } from '@/lib/useAudioRecorder';
import { AlertCircle, Info, Mic, Square, Wifi, WifiOff } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Badge } from './shadcn/ui/badge';
import { Button } from './shadcn/ui/button';
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

  const [showHelp, setShowHelp] = useState(false);

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

  return (
    <div className="space-y-4">
      {/* 接続ステータス */}
      <div className="flex items-center justify-between">
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
        <div className="relative">
          <Button
            variant="ghost"
            size="sm"
            className="text-slate-500 hover:text-slate-700"
            onMouseEnter={() => setShowHelp(true)}
            onMouseLeave={() => setShowHelp(false)}
            onClick={() => setShowHelp(!showHelp)}
          >
            <Info className="w-4 h-4" />
          </Button>
          {showHelp && (
            <div className="absolute right-0 top-8 z-10 w-80 p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg shadow-lg text-xs text-slate-600 dark:text-slate-400 space-y-1">
              <p>• マイクへのアクセス許可が必要です</p>
              <p>• 音声データはリアルタイムでWebSocketサーバーに送信されます</p>
              <p>• ノイズ除去と自動ゲイン制御が有効です</p>
              <p>• VADによる音声区間検出で効率的な文字起こしを実行</p>
            </div>
          )}
        </div>
      </div>

      {/* エラー表示 */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded-lg">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* 録音ボタン */}
      <div className="flex justify-center">
        <Button
          size="lg"
          onClick={isRecording ? handleStopRecording : handleStartRecording}
          className={`
            w-24 h-24 rounded-full transition-all duration-300 
            ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 animate-pulse shadow-lg shadow-red-200'
                : 'bg-blue-500 hover:bg-blue-600 shadow-lg shadow-blue-200'
            }
          `}
          disabled={!isConnected && isRecording}
        >
          {isRecording ? (
            <Square className="w-6 h-6 text-white" />
          ) : (
            <Mic className="w-6 h-6 text-white" />
          )}
        </Button>
      </div>

      <div className="text-center">
        <div className="text-lg font-medium text-slate-900 dark:text-white">
          {isRecording ? '録音中...' : '待機中'}
        </div>
      </div>

      {/* 音声レベルメーター */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-slate-600 dark:text-slate-400">
          <span>音声レベル</span>
          <span>{Math.round(audioLevel)}%</span>
        </div>
        <Progress value={audioLevel} className="w-full h-2" />
      </div>
    </div>
  );
}
