'use client';

import { useAudioRecorder } from '@/lib/useAudioRecorder';
import {
  AlertCircle,
  Info,
  Mic,
  Square,
  Wifi,
  WifiOff,
  Settings,
  Zap,
  DollarSign,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { Badge } from './shadcn/ui/badge';
import { Button } from './shadcn/ui/button';
import { Progress } from './shadcn/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './shadcn/ui/select';
import type { TranscriptionModel, ModelInfo } from '@/lib/types';
import { AVAILABLE_MODELS } from '@/lib/types';

import type { TranscriptionResult, VADResult } from '@/lib/types';

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
    currentModel,
    startRecording,
    stopRecording,
    connect,
    disconnect,
    selectModel,
  } = useAudioRecorder({
    websocketUrl,
    onTranscriptionResult,
    onVADResult,
    onModelChanged: (model) => {
      console.log('[AudioRecorder] Model changed to:', model);
    },
  });

  const [showHelp, setShowHelp] = useState(false);

  // コストアイコンを取得する関数
  const getCostIcon = (cost: ModelInfo['cost']) => {
    switch (cost) {
      case 'low':
        return <DollarSign className="w-3 h-3 text-green-500" />;
      case 'medium':
        return <DollarSign className="w-3 h-3 text-yellow-500" />;
      case 'high':
        return <DollarSign className="w-3 h-3 text-red-500" />;
      default:
        return <DollarSign className="w-3 h-3 text-gray-500" />;
    }
  };

  // 現在のモデル情報を取得
  const currentModelInfo = AVAILABLE_MODELS.find(
    (model) => model.id === currentModel,
  );

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
    <div className="space-y-3">
      {/* 接続ステータス */}
      <div className="flex items-center justify-between">
        <Badge
          variant={isConnected ? 'default' : 'secondary'}
          className="flex items-center gap-1 text-xs"
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
            className="text-slate-500 hover:text-slate-700 h-6 w-6 p-0"
            onMouseEnter={() => setShowHelp(true)}
            onMouseLeave={() => setShowHelp(false)}
            onClick={() => setShowHelp(!showHelp)}
          >
            <Info className="w-3 h-3" />
          </Button>
          {showHelp && (
            <div className="absolute right-0 top-6 z-10 w-72 p-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg shadow-lg text-xs text-slate-600 dark:text-slate-400 space-y-1">
              <p>• マイクへのアクセス許可が必要です</p>
              <p>• 音声データはリアルタイムでWebSocketサーバーに送信されます</p>
              <p>• ノイズ除去と自動ゲイン制御が有効です</p>
              <p>• VADによる音声区間検出で効率的な文字起こしを実行</p>
            </div>
          )}
        </div>
      </div>

      {/* モデル選択 */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            音声認識モデル
          </span>
          <div className="flex items-center gap-2">
            {(isConnected || isRecording) && (
              <Badge variant="secondary" className="text-xs">
                固定
              </Badge>
            )}
            <Settings className="w-4 h-4 text-slate-500" />
          </div>
        </div>

        <Select
          value={currentModel}
          onValueChange={(value: TranscriptionModel) => selectModel(value)}
          disabled={isConnected || isRecording}
        >
          <SelectTrigger className="w-full">
            <SelectValue>
              <div className="flex items-center gap-2">
                {getCostIcon(currentModelInfo?.cost || 'medium')}
                <span className="text-sm">
                  {currentModelInfo?.name || currentModel}
                </span>
              </div>
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {AVAILABLE_MODELS.map((model) => (
              <SelectItem key={model.id} value={model.id}>
                <div className="flex items-start gap-3 py-1">
                  <div className="flex items-center gap-1 mt-0.5">
                    {getCostIcon(model.cost)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm">{model.name}</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
                      {model.description}
                    </div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {model.features.slice(0, 2).map((feature) => (
                        <span
                          key={feature}
                          className="inline-flex items-center px-1.5 py-0.5 text-xs bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded"
                        >
                          {feature}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* 現在のモデル情報表示 */}
        {currentModelInfo && (
          <div className="text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800 p-2 rounded">
            <div className="font-medium mb-1">
              {currentModelInfo.description}
            </div>
            <div className="flex flex-wrap gap-1">
              {currentModelInfo.features.map((feature) => (
                <span
                  key={feature}
                  className="inline-flex items-center px-1 py-0.5 text-xs bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded"
                >
                  {feature}
                </span>
              ))}
            </div>
            {(isConnected || isRecording) && (
              <div className="mt-2 text-xs text-amber-600 dark:text-amber-400">
                ℹ️ モデルは接続前に選択してください。接続中は変更できません。
              </div>
            )}
          </div>
        )}
      </div>

      {/* エラー表示 */}
      {error && (
        <div className="flex items-center gap-2 p-2 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded-lg">
          <AlertCircle className="w-3 h-3" />
          <span className="text-xs">{error}</span>
        </div>
      )}

      {/* 録音ボタン */}
      <div className="flex justify-center">
        <Button
          size="lg"
          onClick={isRecording ? handleStopRecording : handleStartRecording}
          className={`
            w-16 h-16 rounded-full transition-all duration-300 
            ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 animate-pulse shadow-lg shadow-red-200'
                : 'bg-blue-500 hover:bg-blue-600 shadow-lg shadow-blue-200'
            }
          `}
          disabled={!isConnected && isRecording}
        >
          {isRecording ? (
            <Square className="w-5 h-5 text-white" />
          ) : (
            <Mic className="w-5 h-5 text-white" />
          )}
        </Button>
      </div>

      <div className="text-center">
        <div className="text-base font-medium text-slate-900 dark:text-white">
          {isRecording ? '録音中...' : '待機中'}
        </div>
      </div>

      {/* 音声レベルメーター */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-slate-600 dark:text-slate-400">
          <span>音声レベル</span>
          <span>{Math.round(audioLevel)}%</span>
        </div>
        <Progress value={audioLevel} className="w-full h-1.5" />
      </div>
    </div>
  );
}
