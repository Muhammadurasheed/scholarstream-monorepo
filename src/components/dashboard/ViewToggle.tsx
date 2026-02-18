import { LayoutGrid, List } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ViewToggleProps {
  view: 'grid' | 'list';
  onViewChange: (view: 'grid' | 'list') => void;
}

export const ViewToggle = ({ view, onViewChange }: ViewToggleProps) => {
  return (
    <div className="flex items-center gap-1 rounded-lg bg-muted p-1">
      <Button
        size="sm"
        variant={view === 'grid' ? 'default' : 'ghost'}
        onClick={() => onViewChange('grid')}
        className={cn(
          'h-8 w-8 p-0',
          view === 'grid' && 'bg-primary text-primary-foreground hover:bg-primary/90'
        )}
      >
        <LayoutGrid className="h-4 w-4" />
      </Button>
      <Button
        size="sm"
        variant={view === 'list' ? 'default' : 'ghost'}
        onClick={() => onViewChange('list')}
        className={cn(
          'h-8 w-8 p-0',
          view === 'list' && 'bg-primary text-primary-foreground hover:bg-primary/90'
        )}
      >
        <List className="h-4 w-4" />
      </Button>
    </div>
  );
};
