import { useRef, useEffect, useCallback } from 'react';

/**
 * 自動スクロール機能を提供するカスタムフック
 *
 * @param dependencies - 監視する依存関係の配列（通常は配列データ）
 * @returns スクロールコンテナのref、スクロールハンドラー、手動スクロール関数
 */
export function useAutoScroll<T>(dependencies: T[]) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const wasScrolledToBottomRef = useRef(true); // 初期状態では一番下にいるとみなす

  // スクロール位置が一番下かどうかを判定する関数
  const isScrolledToBottom = () => {
    if (!scrollContainerRef.current) return false;
    const { scrollTop, scrollHeight, clientHeight } =
      scrollContainerRef.current;

    // デバッグ用ログ（必要に応じて削除）
    console.log('スクロール判定:', {
      scrollTop,
      scrollHeight,
      clientHeight,
      isAtBottom: scrollTop + clientHeight >= scrollHeight - 10,
    });

    // 10px程度の誤差を許容
    return scrollTop + clientHeight >= scrollHeight - 10;
  };

  // スクロールイベントハンドラー：ユーザーのスクロール状態を追跡
  const handleScroll = () => {
    wasScrolledToBottomRef.current = isScrolledToBottom();
  };

  // 手動で一番下にスクロールする関数
  const scrollToBottom = useCallback(
    (behavior: 'smooth' | 'instant' = 'smooth') => {
      setTimeout(() => {
        scrollContainerRef.current?.scrollTo({
          top: scrollContainerRef.current.scrollHeight,
          behavior,
        });
      }, 0);
    },
    [],
  );

  // 依存関係が変更されたときの自動スクロール処理
  useEffect(() => {
    if (dependencies.length > 0 && wasScrolledToBottomRef.current) {
      scrollToBottom('smooth');
    }
  }, [dependencies, scrollToBottom]);

  return {
    scrollContainerRef,
    handleScroll,
    scrollToBottom,
    isScrolledToBottom,
  };
}
