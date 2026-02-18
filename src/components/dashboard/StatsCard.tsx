import { LucideIcon } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface StatsCardProps {
  icon: LucideIcon;
  value: string | number;
  label: string;
  iconColor?: string;
  onClick?: () => void;
}

export const StatsCard = ({ icon: Icon, value, label, iconColor = 'text-primary', onClick }: StatsCardProps) => {
  return (
    <Card
      className={cn(
        'p-6 transition-all duration-200',
        onClick && 'cursor-pointer hover:-translate-y-1 hover:shadow-lg'
      )}
      onClick={onClick}
    >
      <div className="flex flex-col gap-3">
        <div className="flex items-start justify-between">
          <div className={cn('rounded-lg bg-muted p-2', iconColor)}>
            <Icon className="h-5 w-5" />
          </div>
        </div>
        <div>
          <div className="text-3xl font-bold text-foreground">{value}</div>
          <p className="text-sm text-muted-foreground">{label}</p>
        </div>
      </div>
    </Card>
  );
};
