import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { CheckCircle2, Clock, AlertCircle, XCircle, ExternalLink, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';
import { apiService } from '@/services/api';
import { ApplicationSubmission } from '@/types/scholarship';

// Map API response to display-friendly format
interface TrackedApplication {
  id: string;
  opportunity_name: string;
  opportunity_url: string;
  organization: string;
  status: 'not_started' | 'in_progress' | 'submitted' | 'under_review' | 'accepted' | 'rejected';
  deadline: string;
  started_at: string;
  submitted_at?: string;
  last_updated: string;
  documents_uploaded: string[];
  essay_drafts: number;
  notes: string;
}

const mapApiToTracked = (app: ApplicationSubmission): TrackedApplication => ({
  id: app.application_id,
  opportunity_name: app.scholarship_name || 'Opportunity',
  opportunity_url: '', // Would need to be added to API response
  organization: '', // Would need to be added to API response
  status: app.status === 'draft' ? 'in_progress' : 
          app.status === 'awarded' ? 'accepted' :
          app.status === 'declined' ? 'rejected' :
          app.status as TrackedApplication['status'],
  deadline: app.decision_date || '',
  started_at: app.submitted_at || '',
  submitted_at: app.submitted_at,
  last_updated: app.submitted_at || '',
  documents_uploaded: app.documents?.map(d => d.file_name) || [],
  essay_drafts: app.essays?.length || 0,
  notes: app.notes || '',
});

const statusConfig = {
  not_started: {
    label: 'Not Started',
    icon: AlertCircle,
    color: 'bg-muted text-muted-foreground',
  },
  in_progress: {
    label: 'In Progress',
    icon: Clock,
    color: 'bg-warning/10 text-warning',
  },
  submitted: {
    label: 'Submitted',
    icon: CheckCircle2,
    color: 'bg-info/10 text-info',
  },
  under_review: {
    label: 'Under Review',
    icon: Clock,
    color: 'bg-primary/10 text-primary',
  },
  accepted: {
    label: 'Accepted',
    icon: CheckCircle2,
    color: 'bg-success/10 text-success',
  },
  rejected: {
    label: 'Rejected',
    icon: XCircle,
    color: 'bg-destructive/10 text-destructive',
  },
};

export default function ApplicationTracker() {
  const { user } = useAuth();
  const [applications, setApplications] = useState<TrackedApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    if (user?.uid) {
      fetchApplications();
    }
  }, [user]);

  const fetchApplications = async () => {
    if (!user?.uid) return;
    
    try {
      // Fetch real applications from API
      const response = await apiService.getUserApplications(user.uid);
      // Map API response to TrackedApplication format
      const tracked = (response.applications || []).map(mapApiToTracked);
      setApplications(tracked);
    } catch (error) {
      console.error('Failed to fetch applications:', error);
      // On error, show empty state (NOT mock data)
      setApplications([]);
    } finally {
      setLoading(false);
    }
  };

  const groupedApplications = {
    all: applications,
    active: applications.filter(app => ['not_started', 'in_progress'].includes(app.status)),
    submitted: applications.filter(app => ['submitted', 'under_review'].includes(app.status)),
    completed: applications.filter(app => ['accepted', 'rejected'].includes(app.status)),
  };

  const renderApplicationCard = (app: TrackedApplication) => {
    const StatusIcon = statusConfig[app.status].icon;
    
    return (
      <Card key={app.id} className="p-6 hover:shadow-lg transition-shadow">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold mb-1">{app.opportunity_name}</h3>
            <p className="text-sm text-muted-foreground">{app.organization}</p>
          </div>
          <Badge className={cn('shrink-0', statusConfig[app.status].color)}>
            <StatusIcon className="w-3 h-3 mr-1" />
            {statusConfig[app.status].label}
          </Badge>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
          <div>
            <span className="text-muted-foreground">Deadline:</span>
            <p className="font-medium">{new Date(app.deadline).toLocaleDateString()}</p>
          </div>
          <div>
            <span className="text-muted-foreground">Started:</span>
            <p className="font-medium">{new Date(app.started_at).toLocaleDateString()}</p>
          </div>
        </div>

        {app.documents_uploaded.length > 0 && (
          <div className="mb-4">
            <span className="text-sm text-muted-foreground">Documents uploaded:</span>
            <div className="flex flex-wrap gap-2 mt-2">
              {app.documents_uploaded.map((doc, i) => (
                <Badge key={i} variant="outline" className="text-xs">
                  <FileText className="w-3 h-3 mr-1" />
                  {doc}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {app.notes && (
          <div className="mb-4 p-3 bg-muted/50 rounded-lg">
            <p className="text-sm">{app.notes}</p>
          </div>
        )}

        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => window.open(app.opportunity_url, '_blank')}
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            View Opportunity
          </Button>
          <Button size="sm">Continue Application</Button>
        </div>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <DashboardHeader />
        <div className="container py-8">
          <div className="animate-pulse space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-48 bg-muted rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader />

      <main className="container py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Application Tracker</h1>
          <p className="text-muted-foreground">
            Track all your scholarship and hackathon applications in one place
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="p-4">
            <p className="text-sm text-muted-foreground">Total Applications</p>
            <p className="text-2xl font-bold">{applications.length}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-muted-foreground">In Progress</p>
            <p className="text-2xl font-bold text-warning">
              {groupedApplications.active.length}
            </p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-muted-foreground">Submitted</p>
            <p className="text-2xl font-bold text-info">
              {groupedApplications.submitted.length}
            </p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-muted-foreground">Accepted</p>
            <p className="text-2xl font-bold text-success">
              {applications.filter(app => app.status === 'accepted').length}
            </p>
          </Card>
        </div>

        {/* Applications List */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="all">All ({applications.length})</TabsTrigger>
            <TabsTrigger value="active">Active ({groupedApplications.active.length})</TabsTrigger>
            <TabsTrigger value="submitted">Submitted ({groupedApplications.submitted.length})</TabsTrigger>
            <TabsTrigger value="completed">Completed ({groupedApplications.completed.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="all">
            {applications.length === 0 ? (
              <Card className="p-12 text-center">
                <AlertCircle className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No Applications Yet</h3>
                <p className="text-muted-foreground mb-4">
                  Start applying to opportunities to track your progress here
                </p>
                <Button onClick={() => (window.location.href = '/dashboard')}>
                  Browse Opportunities
                </Button>
              </Card>
            ) : (
              <div className="space-y-4">
                {applications.map(renderApplicationCard)}
              </div>
            )}
          </TabsContent>

          <TabsContent value="active">
            <div className="space-y-4">
              {groupedApplications.active.length === 0 ? (
                <Card className="p-8 text-center">
                  <p className="text-muted-foreground">No active applications</p>
                </Card>
              ) : (
                groupedApplications.active.map(renderApplicationCard)
              )}
            </div>
          </TabsContent>

          <TabsContent value="submitted">
            <div className="space-y-4">
              {groupedApplications.submitted.length === 0 ? (
                <Card className="p-8 text-center">
                  <p className="text-muted-foreground">No submitted applications</p>
                </Card>
              ) : (
                groupedApplications.submitted.map(renderApplicationCard)
              )}
            </div>
          </TabsContent>

          <TabsContent value="completed">
            <div className="space-y-4">
              {groupedApplications.completed.length === 0 ? (
                <Card className="p-8 text-center">
                  <p className="text-muted-foreground">No completed applications</p>
                </Card>
              ) : (
                groupedApplications.completed.map(renderApplicationCard)
              )}
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
