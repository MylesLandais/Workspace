import { describe, it, expect, beforeAll, afterEach } from 'bun:test';
import { useSearchStore } from './search-store';

describe('useSearchStore', () => {
    beforeAll(() => {
        // Reset store state before all tests
        useSearchStore.getState().resetFilters();
    });

    afterEach(() => {
        // Cleanup: ensure we start fresh after each test
        useSearchStore.getState().resetFilters();
    });

    it('should initialize with default values', () => {
        const state = useSearchStore.getState();
        expect(state.filters.query).toBe('');
        expect(state.filters.categories).toEqual([]);
        expect(state.isFiltersOpen).toBe(false);
    });

    it('should update query', () => {
        const { setQuery } = useSearchStore.getState();
        setQuery('bunny');
        expect(useSearchStore.getState().filters.query).toBe('bunny');
    });

    it('should toggle filters', () => {
        const { toggleFilters } = useSearchStore.getState();
        toggleFilters();
        expect(useSearchStore.getState().isFiltersOpen).toBe(true);
        toggleFilters();
        expect(useSearchStore.getState().isFiltersOpen).toBe(false);
    });

    it('should handle multiple state updates', () => {
        const { setQuery, toggleFilters } = useSearchStore.getState();
        
        // Simulate a complex interaction
        setQuery('test query');
        toggleFilters();
        setQuery('updated query');
        
        const finalState = useSearchStore.getState();
        expect(finalState.filters.query).toBe('updated query');
        expect(finalState.isFiltersOpen).toBe(true);
    });
});
