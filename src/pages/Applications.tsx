import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { apiService } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  ArrowLeft,
  FileText,
  Clock,
  DollarSign,
  TrendingUp,
  Edit,
  Trash2,
  ExternalLink,
  Award,
  Calendar,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { MobileBottomNav } from '@/components/dashboard/MobileBottomNav';
import type { ApplicationSubmission } from '@/types/scholarship';

export default function Applications() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [applications, setApplications] = useState<ApplicationSubmission[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [stats, setStats] = useState({
    total: 0,
    draft: 0,
    submitted: 0,
    awarded: 0,
    total_value: 0,
    total_won: 0,
  });

  useEffect(() => {
    if (!user) return;

    const loadApplications = async () => {
      try {
        setLoading(true);
        const response = await apiService.getUserApplications(user.uid);
        setApplications(response.applications);
        setStats(response.stats);
      } catch (error) {
        console.error('Failed to load applications:', error);
      } finally {
        setLoading(false);
      }
    };

    loadApplications();
  }, [user]);

  const filterApplications = (status?: string) => {
    if (!status || status === 'all') return applications;
    return applications.filter(app => app.status === status);
  };

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'draft':
        return {
          color: 'bg-amber-500/20 text-amber-600 border-amber-500/30',
          icon: Edit,
          label: 'Draft',
          borderColor: 'border-l-amber-500',
        };
      case 'submitted':
        return {
          color: 'bg-blue-500/20 text-blue-600 border-blue-500/30',
          icon: Clock,
          label: 'Submitted',
          borderColor: 'border-l-blue-500',
        };
      case 'under_review':
        return {
          color: 'bg-purple-500/20 text-purple-600 border-purple-500/30',
          icon: FileText,
          label: 'Under Review',
          borderColor: 'border-l-purple-500',
        };
      case 'finalist':
        return {
          color: 'bg-yellow-500/20 text-yellow-600 border-yellow-500/30',
          icon: Award,
          label: 'Finalist',
          borderColor: 'border-l-yellow-500',
        };
      case 'awarded':
        return {
          color: 'bg-green-500/20 text-green-600 border-green-500/30',
          icon: CheckCircle2,
          label: 'Award Won!',
          borderColor: 'border-l-green-500',
        };
      case 'declined':
        return {
          color: 'bg-gray-500/20 text-gray-600 border-gray-500/30',
          icon: XCircle,
          label: 'Not Selected',
          borderColor: 'border-l-gray-500',
        };
      case 'expired':
        return {
          color: 'bg-red-500/20 text-red-600 border-red-500/30',
          icon: AlertCircle,
          label: 'Deadline Passed',
          borderColor: 'border-l-red-500',
        };
      default:
        return {
          color: 'bg-muted text-muted-foreground',
          icon: FileText,
          label: status,
          borderColor: 'border-l-muted',
        };
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading your applications...</p>
        </div>
      </div>
    );
  }

  const filteredApps = filterApplications(activeTab === 'all' ? undefined : activeTab);

  return (
    <div className="min-h-screen bg-background pb-20 md:pb-8">
      {/* Header */}
      <div className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4 mb-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/dashboard')}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Dashboard
            </Button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">My Applications</h1>
              <p className="text-muted-foreground">
                {stats.submitted} submitted, {stats.draft} in progress, {stats.awarded} won
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                  <FileText className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-foreground">{stats.total}</p>
                  <p className="text-sm text-muted-foreground">Total</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-green-500/20 flex items-center justify-center">
                  <DollarSign className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-green-600">
                    ${(stats.total_value / 1000).toFixed(0)}k
                  </p>
                  <p className="text-sm text-muted-foreground">Applied For</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-purple-500/20 flex items-center justify-center">
                  <Award className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-purple-600">{stats.awarded}</p>
                  <p className="text-sm text-muted-foreground">Won</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-amber-500/20 flex items-center justify-center">
                  <TrendingUp className="h-5 w-5 text-amber-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-amber-600">
                    ${(stats.total_won / 1000).toFixed(0)}k
                  </p>
                  <p className="text-sm text-muted-foreground">Won</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3 md:grid-cols-5">
            <TabsTrigger value="all">
              All ({stats.total})
            </TabsTrigger>
            <TabsTrigger value="draft">
              Draft ({stats.draft})
            </TabsTrigger>
            <TabsTrigger value="submitted">
              Submitted ({stats.submitted})
            </TabsTrigger>
            <TabsTrigger value="awarded">
              Won ({stats.awarded})
            </TabsTrigger>
            <TabsTrigger value="declined" className="hidden md:block">
              Archived
            </TabsTrigger>
          </TabsList>

          <div className="mt-6">
            {filteredApps.length === 0 ? (
              <EmptyState status={activeTab} onFindScholarships={() => navigate('/dashboard')} />
            ) : (
              <div className="grid gap-4">
                {filteredApps.map((app) => (
                  <ApplicationCard
                    key={app.application_id}
                    application={app}
                    onView={() => navigate(`/applications/${app.application_id}`)}
                    onContinue={() => navigate(`/apply/${app.scholarship_id}`)}
                    onDelete={async () => {
                      if (window.confirm('Delete this application draft?')) {
                        try {
                          await apiService.deleteApplication(app.application_id);
                          setApplications(apps => apps.filter(a => a.application_id !== app.application_id));
                        } catch (error) {
                          console.error('Failed to delete:', error);
                        }
                      }
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        </Tabs>
      </div>

      <MobileBottomNav />
    </div>
  );
}

function ApplicationCard({
  application,
  onView,
  onContinue,
  onDelete,
}: {
  application: ApplicationSubmission;
  onView: () => void;
  onContinue: () => void;
  onDelete: () => void;
}) {
  const statusConfig = getStatusConfig(application.status);
  const StatusIcon = statusConfig.icon;
  const isDraft = application.status === 'draft';
  const isAwarded = application.status === 'awarded';

  return (
    <Card className={`border-l-4 ${statusConfig.borderColor} hover:shadow-md transition-shadow`}>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <CardTitle className="text-lg">{application.scholarship_name}</CardTitle>
              <Badge variant="outline" className={statusConfig.color}>
                <StatusIcon className="h-3 w-3 mr-1" />
                {statusConfig.label}
              </Badge>
            </div>
            <CardDescription className="flex flex-wrap items-center gap-4 text-sm">
              <span className="flex items-center gap-1">
                <DollarSign className="h-3 w-3" />
                ${application.scholarship_amount.toLocaleString()}
              </span>
              {application.submitted_at && (
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  Submitted {new Date(application.submitted_at).toLocaleDateString()}
                </span>
              )}
              {application.confirmation_number && (
                <span className="font-mono text-xs">#{application.confirmation_number}</span>
              )}
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="flex flex-wrap gap-2">
          {isDraft ? (
            <>
              <Button onClick={onContinue} size="sm" className="gap-2">
                <Edit className="h-4 w-4" />
                Continue Application
              </Button>
              <Button onClick={onDelete} size="sm" variant="ghost" className="gap-2">
                <Trash2 className="h-4 w-4" />
                Delete Draft
              </Button>
            </>
          ) : (
            <>
              <Button onClick={onView} size="sm" variant="outline" className="gap-2">
                <FileText className="h-4 w-4" />
                View Submission
              </Button>
              {isAwarded && application.award_amount && (
                <Badge variant="default" className="bg-green-600 text-white gap-2 px-3 py-1">
                  <Award className="h-4 w-4" />
                  Won ${application.award_amount.toLocaleString()}!
                </Badge>
              )}
            </>
          )}
        </div>

        {application.notes && (
          <p className="mt-4 text-sm text-muted-foreground border-l-2 border-muted pl-3">
            {application.notes}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function EmptyState({ status, onFindScholarships }: { status: string; onFindScholarships: () => void }) {
  const messages = {
    all: {
      title: "No applications yet",
      description: "Start applying to scholarships to see them here",
      cta: "Find Scholarships",
    },
    draft: {
      title: "No drafts in progress",
      description: "When you start an application, you'll see it here",
      cta: "Find Scholarships",
    },
    submitted: {
      title: "No submitted applications",
      description: "Applications you've submitted will appear here",
      cta: "Find Scholarships",
    },
    awarded: {
      title: "No awards yet",
      description: "Keep applying! Awards will show up here when you win",
      cta: "Find More Opportunities",
    },
    declined: {
      title: "No archived applications",
      description: "Declined or expired applications will appear here",
      cta: "Find More Opportunities",
    },
  };

  const message = messages[status as keyof typeof messages] || messages.all;

  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-16 text-center">
        <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <FileText className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold text-foreground mb-2">{message.title}</h3>
        <p className="text-sm text-muted-foreground mb-6 max-w-sm">{message.description}</p>
        <Button onClick={onFindScholarships} className="gap-2">
          <ExternalLink className="h-4 w-4" />
          {message.cta}
        </Button>
      </CardContent>
    </Card>
  );
}

function getStatusConfig(status: string) {
  switch (status) {
    case 'draft':
      return {
        color: 'bg-amber-500/20 text-amber-600 border-amber-500/30',
        icon: Edit,
        label: 'Draft',
        borderColor: 'border-l-amber-500',
      };
    case 'submitted':
      return {
        color: 'bg-blue-500/20 text-blue-600 border-blue-500/30',
        icon: Clock,
        label: 'Submitted',
        borderColor: 'border-l-blue-500',
      };
    case 'under_review':
      return {
        color: 'bg-purple-500/20 text-purple-600 border-purple-500/30',
        icon: FileText,
        label: 'Under Review',
        borderColor: 'border-l-purple-500',
      };
    case 'finalist':
      return {
        color: 'bg-yellow-500/20 text-yellow-600 border-yellow-500/30',
        icon: Award,
        label: 'Finalist',
        borderColor: 'border-l-yellow-500',
      };
    case 'awarded':
      return {
        color: 'bg-green-500/20 text-green-600 border-green-500/30',
        icon: CheckCircle2,
        label: 'Award Won!',
        borderColor: 'border-l-green-500',
      };
    case 'declined':
      return {
        color: 'bg-gray-500/20 text-gray-600 border-gray-500/30',
        icon: XCircle,
        label: 'Not Selected',
        borderColor: 'border-l-gray-500',
      };
    case 'expired':
      return {
        color: 'bg-red-500/20 text-red-600 border-red-500/30',
        icon: AlertCircle,
        label: 'Deadline Passed',
        borderColor: 'border-l-red-500',
      };
    default:
      return {
        color: 'bg-muted text-muted-foreground',
        icon: FileText,
        label: status,
        borderColor: 'border-l-muted',
      };
  }
}
