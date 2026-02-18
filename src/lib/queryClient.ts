import { QueryClient } from '@tanstack/react-query';

/**
 * FAANG-Level React Query Configuration
 * Optimized for performance and offline support
 */

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Caching strategy
      staleTime: 5 * 60 * 1000, // 5 minutes - data is fresh
      gcTime: 30 * 60 * 1000, // 30 minutes - keep in cache (formerly cacheTime)
      
      // Refetch strategy
      refetchOnWindowFocus: false, // Don't refetch on tab switch (expensive for our use case)
      refetchOnMount: false, // Don't refetch if data exists (rely on staleTime)
      refetchOnReconnect: true, // Refetch when internet reconnects
      
      // Retry logic
      retry: 2, // Retry failed requests twice
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
      
      // Performance
      networkMode: 'offlineFirst', // Use cache first, then network
      
      // Error handling
      throwOnError: false, // Don't throw errors globally (handle in components)
    },
    mutations: {
      retry: 1, // Retry mutations once
      networkMode: 'online', // Only run mutations when online
    },
  },
});

/**
 * Prefetch utilities for proactive data loading
 */
export const prefetchUtils = {
  /**
   * Prefetch opportunity details when user hovers over card
   */
  async prefetchOpportunityDetail(opportunityId: string) {
    await queryClient.prefetchQuery({
      queryKey: ['opportunity', opportunityId],
      queryFn: async () => {
        const response = await fetch(`/api/opportunities/${opportunityId}`);
        return response.json();
      },
      staleTime: 10 * 60 * 1000, // Keep for 10 minutes
    });
  },

  /**
   * Prefetch user applications
   */
  async prefetchApplications(userId: string) {
    await queryClient.prefetchQuery({
      queryKey: ['applications', userId],
      queryFn: async () => {
        const response = await fetch(`/api/applications?user_id=${userId}`);
        return response.json();
      },
    });
  },
};

/**
 * Cache invalidation helpers
 */
export const cacheUtils = {
  /**
   * Invalidate opportunities cache (e.g., after discovery)
   */
  invalidateOpportunities(userId: string) {
    queryClient.invalidateQueries({ queryKey: ['scholarships', userId] });
  },

  /**
   * Update opportunity in cache (optimistic update)
   */
  updateOpportunityInCache(opportunityId: string, updates: Partial<any>) {
    queryClient.setQueryData(['opportunity', opportunityId], (old: any) => ({
      ...old,
      ...updates,
    }));
  },

  /**
   * Clear all caches (e.g., on logout)
   */
  clearAllCaches() {
    queryClient.clear();
  },
};
