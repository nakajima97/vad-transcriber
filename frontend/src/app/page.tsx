'use client';

import { AudioRecorder } from '@/components/AudioRecorder';
import { Badge } from '@/components/shadcn/ui/badge';
import { Button } from '@/components/shadcn/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/shadcn/ui/card';
import {
  AlertCircle,
  CheckCircle,
  Clock,
  Copy,
  Download,
  Mic,
  Trash2,
} from 'lucide-react';
import { useState } from 'react';
import { useAutoScroll } from '@/lib/useAutoScroll';

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

export default function VADTranscriberApp() {
  const [transcriptionResults, setTranscriptionResults] = useState<
    TranscriptionResult[]
  >([]);

  // 自動スクロール機能を使用
  const { scrollContainerRef, handleScroll } =
    useAutoScroll(transcriptionResults);

  const handleTranscriptionResult = (result: TranscriptionResult) => {
    setTranscriptionResults((prev) => [...prev, result]);
  };

  const handleVADResult = (result: VADResult) => {
    // VAD結果は表示しないが、コールバック関数として残す
    console.log('VAD result:', result);
  };

  const handleClearTranscription = () => {
    setTranscriptionResults([]);
  };

  return (
    <div className="h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800 flex flex-col">
      {/* Header */}
      <header className="border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:bg-slate-900/95 flex-shrink-0">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Mic className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                  VAD Transcriber
                </h1>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  リアルタイム音声文字起こし
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="outline">リアルタイム版</Badge>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-4 flex-1 flex flex-col overflow-hidden">
        {/* メイン横2分割レイアウト */}
        <div className="flex flex-col md:flex-row gap-6 flex-1 overflow-hidden">
          {/* モバイル時は録音開始セクションを上に配置 */}
          <div className="md:hidden flex-shrink-0">
            <Card className="bg-white dark:bg-slate-800 border-0 shadow-lg">
              <CardHeader className="pb-3 pt-4">
                <CardTitle className="text-base">録音開始</CardTitle>
              </CardHeader>
              <CardContent className="pt-0 pb-4">
                <AudioRecorder
                  websocketUrl="ws://localhost:8000/ws"
                  onTranscriptionResult={handleTranscriptionResult}
                  onVADResult={handleVADResult}
                />
              </CardContent>
            </Card>
          </div>

          {/* 左側: 文字起こし結果 (デスクトップ: 幅60%, モバイル: 100%) */}
          <div className="w-full md:w-3/5 flex flex-col flex-1 min-h-0">
            <Card className="bg-white dark:bg-slate-800 border-0 shadow-lg flex flex-col h-full">
              <CardHeader className="flex flex-col space-y-4 flex-shrink-0">
                <div>
                  <CardTitle>文字起こし結果</CardTitle>
                  <CardDescription>
                    音声認識の結果がリアルタイムで表示されます
                  </CardDescription>
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleClearTranscription}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    クリア
                  </Button>
                  <Button variant="outline" size="sm">
                    <Download className="w-4 h-4 mr-2" />
                    エクスポート
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="flex-1 min-h-0 flex flex-col">
                <div
                  ref={scrollContainerRef}
                  className="flex-1 overflow-y-auto space-y-3"
                  onScroll={handleScroll}
                >
                  {transcriptionResults.length === 0 ? (
                    <div className="text-center py-8 text-slate-500 dark:text-slate-400 h-full flex flex-col items-center justify-center">
                      <Mic className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                      <p>録音を開始すると文字起こし結果がここに表示されます</p>
                    </div>
                  ) : (
                    transcriptionResults.map((result) => (
                      <div
                        key={result.id}
                        className={`p-4 rounded-lg border-l-4 ${
                          result.is_final
                            ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                            : 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="text-slate-900 dark:text-white font-medium">
                              {result.text}
                            </p>
                            <div className="flex items-center space-x-4 mt-2 text-sm text-slate-600 dark:text-slate-400">
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {new Date(
                                  result.timestamp * 1000,
                                ).toLocaleTimeString('ja-JP')}
                              </span>
                              <span className="flex items-center gap-1">
                                {result.is_final ? (
                                  <CheckCircle className="w-3 h-3 text-green-600" />
                                ) : (
                                  <AlertCircle className="w-3 h-3 text-yellow-600" />
                                )}
                                確信度: {Math.round(result.confidence * 100)}%
                              </span>
                              <span className="text-xs text-slate-500">
                                セグメント: {result.segment_id}
                              </span>
                            </div>
                          </div>
                          <Button variant="ghost" size="sm">
                            <Copy className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 右側: その他の機能 (デスクトップのみ表示: 幅40%) */}
          <div className="hidden md:flex md:w-2/5 flex-col space-y-6">
            {/* 録音開始セクション */}
            <div className="flex-shrink-0">
              <Card className="bg-white dark:bg-slate-800 border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="text-lg">録音開始</CardTitle>
                </CardHeader>
                <CardContent>
                  <AudioRecorder
                    websocketUrl="ws://localhost:8000/ws"
                    onTranscriptionResult={handleTranscriptionResult}
                    onVADResult={handleVADResult}
                  />
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
