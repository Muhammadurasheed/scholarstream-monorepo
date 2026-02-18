import { Scholarship } from '@/types/scholarship';
import { OpportunityCard } from './OpportunityCard';
import { useScholarships } from '@/hooks/useScholarships';
import { cn } from '@/lib/utils';

interface SimpleOpportunityGridProps {
  opportunities: Scholarship[];
  view?: 'grid' | 'list';
  className?: string;
  justFlushedIds?: Set<string>;
}

/**
 * Simple CSS Grid-based opportunity display (no virtualization)
 * Used with pagination for better UX and SEO
 */
export const SimpleOpportunityGrid = ({ 
  opportunities, 
  view = 'grid',
  className,
  justFlushedIds = new Set(),
}: SimpleOpportunityGridProps) => {
  const { savedScholarshipIds, toggleSaveScholarship, startApplication } = useScholarships();

  if (opportunities.length === 0) {
    return null;
  }

  return (
    <div 
      className={cn(
        view === 'grid' 
          ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6'
          : 'flex flex-col gap-4',
        className
      )}
    >
      {opportunities.map((scholarship) => (
        <OpportunityCard
          key={scholarship.id}
          scholarship={scholarship}
          isSaved={savedScholarshipIds.has(scholarship.id)}
          onToggleSave={toggleSaveScholarship}
          onStartApplication={startApplication}
          isJustAdded={justFlushedIds.has(scholarship.id)}
        />
      ))}
    </div>
  );
};
