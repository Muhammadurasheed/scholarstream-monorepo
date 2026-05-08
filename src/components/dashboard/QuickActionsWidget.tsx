import { User, FileText, ClipboardList, Bookmark, ChevronRight, Briefcase } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

interface QuickAction {
  id: string;
  icon: React.ElementType;
  title: string;
  description: string;
  action: string;
  path?: string;
  variant?: 'default' | 'outline';
}

export const QuickActionsWidget = () => {
  const navigate = useNavigate();

  const actions: QuickAction[] = [
    {
      id: 'cv-builder',
      icon: Briefcase,
      title: 'Application Builder',
      description: 'Build your universal application profile',
      action: 'Build',
      path: '/profile?tab=resume',
      variant: 'default',
    },
    {
      id: 'tracker',
      icon: ClipboardList,
      title: 'Application Tracker',
      description: 'Track all your applications',
      action: 'View',
      path: '/application-tracker',
      variant: 'outline',
    },
    {
      id: 'saved',
      icon: Bookmark,
      title: 'Saved Opportunities',
      description: 'View your bookmarked opportunities',
      action: 'View',
      path: '/saved',
      variant: 'outline',
    },
    {
      id: 'profile',
      icon: User,
      title: 'Complete Profile',
      description: 'Improve your match score',
      action: 'Update',
      path: '/profile',
      variant: 'outline',
    },
  ];

  const handleAction = (action: QuickAction) => {
    if (action.path) {
      navigate(action.path);
    } else {
      console.log(`Action: ${action.id}`);
    }
  };

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
      <div className="space-y-3">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <div
              key={action.id}
              className="flex items-start gap-3 p-3 rounded-lg border border-border hover:bg-muted/30 transition-colors cursor-pointer"
              onClick={() => handleAction(action)}
            >
              <div className="shrink-0 mt-0.5">
                <div className="rounded-lg bg-primary/10 p-2">
                  <Icon className="h-4 w-4 text-primary" />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-foreground text-sm mb-0.5">{action.title}</div>
                <div className="text-xs text-muted-foreground">{action.description}</div>
              </div>
              <Button
                variant={action.variant}
                size="sm"
                className="shrink-0"
                onClick={(e) => {
                  e.stopPropagation();
                  handleAction(action);
                }}
              >
                <span className="hidden sm:inline">{action.action}</span>
                <ChevronRight className="h-4 w-4 sm:hidden" />
              </Button>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
