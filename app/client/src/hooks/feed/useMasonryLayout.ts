import { useMemo } from 'react';

interface Position {
    x: number;
    y: number;
}

export function useMasonryLayout<T extends { id: string }>(
    items: T[],
    columnCount: number,
    columnWidth: number,
    gap: number,
    measuredHeights: Record<string, number>,
    defaultAspectRatio: number = 1.5
) {
    return useMemo(() => {
        const colHeights = new Array(columnCount).fill(0);
        const itemPositions: Record<string, Position> = {};

        items.forEach((item) => {
            let shortestColIndex = 0;
            let minHeight = colHeights[0];

            for (let i = 1; i < columnCount; i++) {
                if (colHeights[i] < minHeight) {
                    minHeight = colHeights[i];
                    shortestColIndex = i;
                }
            }

            const x = shortestColIndex * (columnWidth + gap);
            const y = colHeights[shortestColIndex];

            itemPositions[item.id] = { x, y };

            const height = measuredHeights[item.id] || (columnWidth * defaultAspectRatio);
            colHeights[shortestColIndex] += height + gap;
        });

        const containerHeight = Math.max(...colHeights, 0);

        return {
            itemPositions,
            containerHeight,
        };
    }, [items, columnCount, columnWidth, gap, measuredHeights, defaultAspectRatio]);
}
