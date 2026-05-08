import { FixedSizeList } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import { Scholarship } from '@/types/scholarship';
import { ScholarshipCard } from './ScholarshipCard';
import { useScholarships } from '@/hooks/useScholarships';
import { cn } from '@/lib/utils';
import { useMemo } from 'react';

interface OpportunityGridProps {
    opportunities: Scholarship[];
    view?: 'grid' | 'list';
}

export const OpportunityGrid = ({ opportunities, view = 'grid' }: OpportunityGridProps) => {
    const { savedScholarshipIds, toggleSaveScholarship, startApplication } = useScholarships();

    return (
        <div className="h-[calc(100vh-250px)] w-full min-h-[500px]">
            <AutoSizer>
                {({ height, width }) => {
                    // Constants
                    const ROW_HEIGHT = view === 'grid' ? 420 : 250;
                    const GUTTER = 16;

                    // Responsive Column Logic
                    let itemsPerRow = 1;
                    if (view === 'grid') {
                        if (width >= 1200) itemsPerRow = 3;
                        else if (width >= 768) itemsPerRow = 2;
                        else itemsPerRow = 1;
                    }

                    const rowCount = Math.ceil(opportunities.length / itemsPerRow);
                    const itemWidth = (width - (GUTTER * (itemsPerRow - 1))) / itemsPerRow;

                    return (
                        <FixedSizeList
                            height={height}
                            width={width}
                            itemCount={rowCount}
                            itemSize={ROW_HEIGHT}
                            className={cn("scrollbar-hide", view === 'grid' ? '' : 'p-0')}
                        >
                            {({ index, style }) => {
                                const startIndex = index * itemsPerRow;
                                const items = opportunities.slice(startIndex, startIndex + itemsPerRow);

                                return (
                                    <div style={{
                                        ...style,
                                        width: style.width,
                                        height: (style.height as number) - GUTTER
                                    }} className="flex gap-4">
                                        {items.map((scholarship) => (
                                            <div key={scholarship.id} style={{ width: itemWidth, height: '100%' }}>
                                                <ScholarshipCard
                                                    scholarship={scholarship}
                                                    isSaved={savedScholarshipIds.has(scholarship.id)}
                                                    onToggleSave={toggleSaveScholarship}
                                                    onStartApplication={startApplication}
                                                />
                                            </div>
                                        ))}
                                    </div>
                                );
                            }}
                        </FixedSizeList>
                    );
                }}
            </AutoSizer>
        </div>
    );
};
