import { Scholarship } from '@/types/scholarship';
import { SimpleOpportunityGrid } from './SimpleOpportunityGrid';
import { Pagination } from './Pagination';
import { usePaginatedOpportunities } from '@/hooks/usePaginatedOpportunities';
import { useEffect } from 'react';
import { SkeletonCard } from '@/components/ui/SkeletonCard';

interface PaginatedGridProps {
  opportunities: Scholarship[];
  view?: 'grid' | 'list';
  itemsPerPage?: number;
  loading?: boolean;
  justFlushedIds?: Set<string>;
}

/**
 * Paginated grid component that replaces virtualization
 * Better UX, SEO-friendly, and works on all devices
 */
export const PaginatedGrid = ({
  opportunities,
  view = 'grid',
  itemsPerPage = 12,
  loading = false,
  justFlushedIds = new Set(),
}: PaginatedGridProps) => {
  const {
    paginatedItems,
    currentPage,
    totalPages,
    totalItems,
    goToPage,
    resetPage,
  } = usePaginatedOpportunities(opportunities, itemsPerPage);

  // Reset to page 1 when opportunities list changes
  useEffect(() => {
    resetPage();
  }, [opportunities.length, resetPage]);

  // Scroll to top of grid when page changes
  useEffect(() => {
    const section = document.getElementById('opportunities-section');
    if (section && currentPage > 1) {
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [currentPage]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {Array.from({ length: itemsPerPage }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Results count */}
      {totalItems > 0 && (
        <div className="text-sm text-muted-foreground">
          Showing {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, totalItems)} of {totalItems} opportunities
        </div>
      )}

      {/* Grid */}
      <SimpleOpportunityGrid 
        opportunities={paginatedItems} 
        view={view}
        justFlushedIds={justFlushedIds}
      />

      {/* Pagination */}
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
