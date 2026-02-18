import { Sparkles, FileText, Clock, CheckCircle, Upload, TrendingUp } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { getTimeAgo } from '@/utils/scholarshipUtils';

interface Activity {
  id: string;
  type: 'new' | 'draft' | 'deadline' | 'success' | 'upload' | 'update';
  icon: React.ElementType;
  iconColor: string;
  title: string;
  description: string;
  timestamp: string;
}

export const ActivityFeedWidget = () => {
  const activities: Activity[] = [
    {
      id: '1',
      type: 'new',
      icon: Sparkles,
      iconColor: 'text-primary',
      title: 'New scholarship discovered',
      description: '"Gates Millennium" matches you at 92%',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: '2',
      type: 'draft',
      icon: FileText,
      iconColor: 'text-info',
      title: 'Application draft saved',
      description: '"Dell Scholars Program"',
      timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: '3',
      type: 'deadline',
      icon: Clock,
      iconColor: 'text-warning',
      title: 'Deadline approaching',
      description: '"Coca-Cola Scholars" due in 5 days',
      timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: '4',
      type: 'upload',
      icon: Upload,
      iconColor: 'text-success',
      title: 'Document uploaded',
      description: 'Transcript uploaded successfully',
      timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    },
    {
      id: '5',
      type: 'update',
      icon: TrendingUp,
      iconColor: 'text-primary',
      title: 'Profile updated',
      description: 'GPA added - 15 new matches found',
      timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    },
  ];

  const getIconBadge = (activity: Activity) => {
    const Icon = activity.icon;
    return (
      <div className={`rounded-full bg-muted p-2 ${activity.iconColor}`}>
        <Icon className="h-3.5 w-3.5" />
      </div>
    );
  };

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
      <div className="space-y-4">
        {activities.map((activity, index) => (
          <div key={activity.id} className="relative">
            <div className="flex gap-3">
              {getIconBadge(activity)}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-foreground mb-0.5">{activity.title}</div>
                <div className="text-xs text-muted-foreground mb-1">{activity.description}</div>
                <div className="text-xs text-muted-foreground">{getTimeAgo(activity.timestamp)}</div>
              </div>
            </div>
            {index < activities.length - 1 && (
              <div className="absolute left-[18px] top-10 bottom-0 w-px bg-border" />
            )}
          </div>
        ))}
      </div>
      <Button variant="ghost" className="w-full mt-4" size="sm">
        View All Activity
      </Button>
    </Card>
  );
};
