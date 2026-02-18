import { Scholarship } from '@/types/scholarship';
import { OpportunityGrid } from './OpportunityGrid';
import { Pagination } from './Pagination';
import { usePaginatedOpportunities } from '@/hooks/usePaginatedOpportunities';
import { useEffect } from 'react';

interface PaginatedOpportunitySectionProps {
  opportunities: Scholarship[];
  view: 'grid' | 'list';
  itemsPerPage?: number;
}

/**
 * Reusable component for paginated opportunity lists
 * Used in Dashboard tabs for consistent pagination behavior
 */
export const PaginatedOpportunitySection = ({
  opportunities,
  view,
  itemsPerPage = 12,
}: PaginatedOpportunitySectionProps) => {
  const {
    paginatedItems,
    currentPage,
    totalPages,
    goToPage,
    resetPage,
  } = usePaginatedOpportunities(opportunities, itemsPerPage);

  // Reset to page 1 when opportunities list changes (e.g., new filter)
  useEffect(() => {
    resetPage();
  }, [opportunities.length, resetPage]);

  return (
    <div className="space-y-6">
      <OpportunityGrid opportunities={paginatedItems} view={view} />
      {totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={goToPage}
        />
      )}
    </div>
  );
};