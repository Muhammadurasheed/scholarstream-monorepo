import { FixedSizeList as List } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import { Scholarship } from '@/types/scholarship';
import { ScholarshipCard } from './ScholarshipCard';
import { useScholarships } from '@/hooks/useScholarships';
import { cn } from '@/lib/utils';
import { useMemo } from 'react';

interface VirtualizedGridProps {
    opportunities: Scholarship[];
    view?: 'grid' | 'list';
}

export const VirtualizedGrid = ({ opportunities, view = 'grid' }: VirtualizedGridProps) => {
    const { savedScholarshipIds, toggleSaveScholarship, startApplication } = useScholarships();

    // Grid Setup
    const COLUMN_COUNT = view === 'grid' ? 3 : 1;
    const ROW_HEIGHT = 320; // Approximation - adjust based on card height
    const GUTTER = 16;

    const Row = ({ index, style, width }: { index: number, style: any, width: number }) => {
        const startIndex = index * COLUMN_COUNT;
        const items = opportunities.slice(startIndex, startIndex + COLUMN_COUNT);

        // Calculate dynamic width for grid items to account for gutter
        const itemWidth = view === 'grid'
            ? (width - (GUTTER * (COLUMN_COUNT - 1))) / COLUMN_COUNT
            : width;

        return (
            <div style={style} className="flex gap-4">
                {items.map((scholarship) => (
                    <div key={scholarship.id} style={{ width: itemWidth }}>
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
    };

    if (opportunities.length === 0) {
        return (
            <div className="text-center py-12 border border-dashed rounded-xl bg-muted/30">
                <p className="text-muted-foreground">No opportunities found in this category.</p>
            </div>
        );
    }

    return (
        <div className="h-[800px] w-full">
            <AutoSizer>
                {({ height, width }) => (
                    <List
                        height={height}
                        width={width}
                        itemCount={Math.ceil(opportunities.length / COLUMN_COUNT)}
                        itemSize={ROW_HEIGHT}
                        className={cn("scrollbar-hide", view === 'grid' ? '' : 'p-0')}
                    >
                        {({ index, style }) => <Row index={index} style={style} width={width} />}
                    </List>
                )}
            </AutoSizer>
        </div>
    );
};
