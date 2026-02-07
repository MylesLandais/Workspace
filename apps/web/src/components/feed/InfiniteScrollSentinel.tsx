"use client";

import { useEffect, useRef, useCallback } from "react";

interface InfiniteScrollSentinelProps {
  onIntersect: () => void;
  enabled?: boolean;
  rootMargin?: string;
}

export function InfiniteScrollSentinel({
  onIntersect,
  enabled = true,
  rootMargin = "200px",
}: InfiniteScrollSentinelProps) {
  const sentinelRef = useRef<HTMLDivElement>(null);
  const onIntersectRef = useRef(onIntersect);

  // Keep callback ref updated
  useEffect(() => {
    onIntersectRef.current = onIntersect;
  }, [onIntersect]);

  const handleIntersect = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries;
      if (entry.isIntersecting && enabled) {
        onIntersectRef.current();
      }
    },
    [enabled],
  );

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(handleIntersect, {
      rootMargin,
      threshold: 0,
    });

    observer.observe(sentinel);

    return () => {
      observer.disconnect();
    };
  }, [handleIntersect, rootMargin]);

  return <div ref={sentinelRef} className="h-1 w-full" aria-hidden="true" />;
}
