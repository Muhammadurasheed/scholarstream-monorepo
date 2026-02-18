import { useState, useMemo, useCallback } from 'react';
import { Scholarship } from '@/types/scholarship';

/**
 * Hook for paginating any filtered opportunity list
 * Used by Dashboard tabs for scholarships, hackathons, bounties, competitions
 */
export const usePaginatedOpportunities = (
  opportunities: Scholarship[],
  itemsPerPage: number = 12
) => {
  const [currentPage, setCurrentPage] = useState(1);

  // Reset to page 1 when opportunities change (e.g., filter/search)
  const totalPages = Math.ceil(opportunities.length / itemsPerPage);

  // Ensure current page is valid
  const validCurrentPage = Math.min(currentPage, Math.max(1, totalPages));

  const paginatedItems = useMemo(() => {
    const startIndex = (validCurrentPage - 1) * itemsPerPage;
    return opportunities.slice(startIndex, startIndex + itemsPerPage);
  }, [opportunities, validCurrentPage, itemsPerPage]);

  const goToPage = useCallback((page: number) => {
    const newPage = Math.max(1, Math.min(page, totalPages));
    setCurrentPage(newPage);
  }, [totalPages]);

  const resetPage = useCallback(() => {
    setCurrentPage(1);
  }, []);

  return {
    paginatedItems,
    currentPage: validCurrentPage,
    totalPages,
    totalItems: opportunities.length,
    goToPage,
    resetPage,
    hasNextPage: validCurrentPage < totalPages,
    hasPrevPage: validCurrentPage > 1,
  };
};