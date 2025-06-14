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
import { Progress } from '@/components/shadcn/ui/progress';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/shadcn/ui/tabs';
import {
  AlertCircle,
  CheckCircle,
  Clock,
  Copy,
  Download,
  Eye,
  Info,
  Languages,
  Mic,
  Settings,
  Trash2,
  User,
  Volume2,
} from 'lucide-react';
import { useState } from 'react';

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
  const [vadResults, setVadResults] = useState<VADResult[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState('ja');
  const [vadSensitivity, setVadSensitivity] = useState(0.5);

  const handleTranscriptionResult = (result: TranscriptionResult) => {
    setTranscriptionResults((prev) => [...prev, result]);
  };

  const handleVADResult = (result: VADResult) => {
    setVadResults((prev) => [...prev.slice(-10), result]);
  };

  const handleClearTranscription = () => {
    setTranscriptionResults([]);
    setVadResults([]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:bg-slate-900/95">
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

      <main className="container mx-auto px-4 py-8">
        {/* メイン制御パネル */}
        <div className="mb-8">
          <AudioRecorder
            websocketUrl="ws://localhost:8000/ws"
            onTranscriptionResult={handleTranscriptionResult}
            onVADResult={handleVADResult}
          />
        </div>

        {/* 統計情報 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="flex items-center space-x-3 p-4 bg-white dark:bg-slate-800 rounded-lg shadow-lg">
            <Eye className="w-5 h-5 text-slate-600 dark:text-slate-400" />
            <div>
              <p className="text-sm font-medium text-slate-900 dark:text-white">
                認識結果
              </p>
              <p className="text-lg font-bold text-green-600">
                {transcriptionResults.length}件
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3 p-4 bg-white dark:bg-slate-800 rounded-lg shadow-lg">
            <Languages className="w-5 h-5 text-slate-600 dark:text-slate-400" />
            <div>
              <p className="text-sm font-medium text-slate-900 dark:text-white">
                言語
              </p>
              <p className="text-lg font-bold text-purple-600">日本語</p>
            </div>
          </div>

          <div className="flex items-center space-x-3 p-4 bg-white dark:bg-slate-800 rounded-lg shadow-lg">
            <Volume2 className="w-5 h-5 text-slate-600 dark:text-slate-400" />
            <div>
              <p className="text-sm font-medium text-slate-900 dark:text-white">
                VAD検出
              </p>
              <p className="text-lg font-bold text-blue-600">
                {vadResults.length}回
              </p>
            </div>
          </div>
        </div>

        {/* タブセクション */}
        <Tabs defaultValue="transcription" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 bg-white dark:bg-slate-800 shadow-sm">
            <TabsTrigger value="transcription">文字起こし結果</TabsTrigger>
            <TabsTrigger value="vad">VAD状態</TabsTrigger>
            <TabsTrigger value="settings">設定</TabsTrigger>
          </TabsList>

          {/* 文字起こし結果タブ */}
          <TabsContent value="transcription" className="space-y-4">
            <Card className="bg-white dark:bg-slate-800 border-0 shadow-lg">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>リアルタイム文字起こし</CardTitle>
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
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {transcriptionResults.length === 0 ? (
                    <div className="text-center py-8 text-slate-500 dark:text-slate-400">
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
          </TabsContent>

          {/* VAD状態タブ */}
          <TabsContent value="vad" className="space-y-4">
            <Card className="bg-white dark:bg-slate-800 border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Volume2 className="w-5 h-5 text-orange-600" />
                  Voice Activity Detection
                </CardTitle>
                <CardDescription>
                  発話区間の検出状況をリアルタイムで表示
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* 現在のVAD状態 */}
                  <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-slate-900 dark:text-white">
                        現在の状態
                      </span>
                      <div className="flex items-center space-x-2">
                        <div
                          className={`w-3 h-3 rounded-full ${
                            vadResults.length > 0 &&
                            vadResults[vadResults.length - 1]?.is_speech
                              ? 'bg-green-500 animate-pulse'
                              : 'bg-slate-400'
                          }`}
                        />
                        <span className="text-sm text-slate-600 dark:text-slate-400">
                          {vadResults.length > 0 &&
                          vadResults[vadResults.length - 1]?.is_speech
                            ? '発話中'
                            : '無音'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* VAD履歴 */}
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {vadResults.length === 0 ? (
                      <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                        <Volume2 className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                        <p>録音開始後、VAD状態がここに表示されます</p>
                      </div>
                    ) : (
                      vadResults
                        .slice(-10)
                        .reverse()
                        .map((vad) => (
                          <div
                            key={vad.timestamp}
                            className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700 rounded-lg"
                          >
                            <div className="flex items-center space-x-3">
                              <div
                                className={`w-2 h-2 rounded-full ${
                                  vad.is_speech
                                    ? 'bg-green-500'
                                    : 'bg-slate-400'
                                }`}
                              />
                              <span className="text-sm font-medium text-slate-900 dark:text-white">
                                {vad.is_speech ? '発話検出' : '無音'}
                              </span>
                            </div>
                            <div className="text-sm text-slate-600 dark:text-slate-400 space-x-4">
                              <span>
                                確信度: {Math.round(vad.confidence * 100)}%
                              </span>
                              <span>
                                {new Date(
                                  vad.timestamp * 1000,
                                ).toLocaleTimeString('ja-JP')}
                              </span>
                            </div>
                          </div>
                        ))
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 設定タブ */}
          <TabsContent value="settings" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="bg-white dark:bg-slate-800 border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="w-5 h-5 text-slate-600" />
                    音声設定
                  </CardTitle>
                  <CardDescription>音声入力と処理の設定</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-slate-900 dark:text-white">
                      言語設定
                    </label>
                    <select
                      className="w-full mt-2 p-2 border rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
                      value={selectedLanguage}
                      onChange={(e) => setSelectedLanguage(e.target.value)}
                    >
                      <option value="ja">日本語</option>
                      <option value="en">English</option>
                      <option value="zh">中文</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-slate-900 dark:text-white">
                      サンプリングレート
                    </label>
                    <select className="w-full mt-2 p-2 border rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-white">
                      <option value="16000">16kHz (推奨)</option>
                      <option value="22050">22.05kHz</option>
                      <option value="44100">44.1kHz</option>
                    </select>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white dark:bg-slate-800 border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Volume2 className="w-5 h-5 text-orange-600" />
                    VAD設定
                  </CardTitle>
                  <CardDescription>音声検出の感度調整</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-slate-900 dark:text-white">
                        検出感度
                      </label>
                      <span className="text-sm text-slate-600 dark:text-slate-400">
                        {Math.round(vadSensitivity * 100)}%
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={vadSensitivity}
                      onChange={(e) =>
                        setVadSensitivity(Number.parseFloat(e.target.value))
                      }
                      className="w-full"
                    />
                  </div>

                  <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-700">
                    <div className="flex">
                      <Info className="w-4 h-4 text-blue-600 mt-0.5 mr-2 flex-shrink-0" />
                      <div className="text-sm text-blue-800 dark:text-blue-200">
                        <p className="font-medium mb-1">設定のガイドライン</p>
                        <p>低い値: 静かな環境での使用に適している</p>
                        <p>高い値: ノイズの多い環境での使用に適している</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
