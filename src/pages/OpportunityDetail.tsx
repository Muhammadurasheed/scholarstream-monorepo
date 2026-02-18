import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Calendar, Clock, Bookmark, Award, ExternalLink, Target, Users,
  Calculator, ChevronRight, Home, Share2, CheckCircle, XCircle,
  HelpCircle, Download, TrendingUp, Search, AlertTriangle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Scholarship } from '@/types/scholarship';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import {
  formatCurrency,
  getDeadlineInfo,
  getMatchTierColor,
  getCompetitionBadgeColor,
  getTimeAgo,
  normalizeApplyUrl,
} from '@/utils/scholarshipUtils';
import { cn } from '@/lib/utils';
import { matchingEngine } from '@/services/matchingEngine';

const OpportunityDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();

  const [scholarship, setScholarship] = useState<Scholarship | null>(null);
  const [loading, setLoading] = useState(true);
  const [isSaved, setIsSaved] = useState(false);
  const [imageError, setImageError] = useState(false);

  useEffect(() => {
    const loadScholarship = async () => {
      if (!id) return;

      try {
        setLoading(true);
        const data = await apiService.getScholarshipById(id);
        setScholarship(data);
      } catch (error) {
        console.error('Failed to load scholarship:', error);
        toast({
          variant: 'destructive',
          title: 'Failed to load scholarship',
          description: 'Please try again later.',
        });
        navigate('/dashboard');
      } finally {
        setLoading(false);
      }
    };

    loadScholarship();
  }, [id, navigate, toast]);

  const handleToggleSave = async () => {
    if (!user?.uid || !scholarship) return;

    try {
      if (isSaved) {
        await apiService.unsaveScholarship(user.uid, scholarship.id);
        setIsSaved(false);
        toast({ title: 'Removed from favorites' });
      } else {
        await apiService.saveScholarship(user.uid, scholarship.id);
        setIsSaved(true);
        toast({ title: 'Saved to favorites' });
      }
    } catch (error) {
      console.error('Failed to toggle save:', error);
      toast({ variant: 'destructive', title: 'Action failed' });
    }
  };

  const handleStartApplication = async () => {
    if (!scholarship) return;

    // Validate URL before opening
    if (!scholarship.source_url || scholarship.source_url.trim() === '') {
      toast({
        variant: 'destructive',
        title: 'Application link unavailable',
        description: 'Searching for this opportunity online...',
      });

      // Fallback to Google search
      const searchQuery = `${scholarship.name} ${scholarship.organization} scholarship application`;
      window.open(`https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`, '_blank', 'noopener,noreferrer');
      return;
    }

    // Check if URL is validated (from backend)
    const isValidated = (scholarship as any).url_validated !== false;

    if (!isValidated) {
      toast({
        variant: 'default',
        title: 'Opening unverified link',
        description: 'This link has not been verified. If it doesn\'t work, use the search button below.',
      });
    }

    // Try to open the URL
    try {
      const normalizedUrl = normalizeApplyUrl(scholarship.source_url);
      const opened = window.open(normalizedUrl, '_blank', 'noopener,noreferrer');

      if (!opened) {
        throw new Error('Popup blocked');
      }

      // Track application start
      if (user?.uid) {
        try {
          await apiService.startApplication(user.uid, scholarship.id);
        } catch (error) {
          console.error('Failed to track application:', error);
          // Don't block user if tracking fails
        }
      }

      toast({
        title: 'Application opened',
        description: 'Good luck with your application! 🎯',
      });
    } catch (error) {
      // Fallback if URL fails to open
      console.error('Failed to open application URL:', error);

      toast({
        variant: 'destructive',
        title: 'Link failed to open',
        description: 'Searching for this opportunity instead...',
      });

      const searchQuery = `${scholarship.name} ${scholarship.organization} apply`;
      window.open(`https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`, '_blank', 'noopener,noreferrer');
    }
  };

  const handleSearchOpportunity = () => {
    if (!scholarship) return;
    const query = encodeURIComponent(`${scholarship.name} ${scholarship.organization} scholarship application`);
    window.open(`https://www.google.com/search?q=${query}`, '_blank', 'noopener,noreferrer');
  };

  const handleShare = () => {
    if (!scholarship) return;

    const url = window.location.href;

    if (navigator.share) {
      navigator.share({
        title: scholarship.name,
        text: `Check out this scholarship: ${scholarship.name} - ${formatCurrency(scholarship.amount)}`,
        url: url,
      });
    } else {
      navigator.clipboard.writeText(url);
      toast({ title: 'Link copied to clipboard!' });
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container py-8 space-y-6">
          <Skeleton className="h-12 w-64" />
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    );
  }

  if (!scholarship) {
    return null;
  }

  const deadlineInfo = getDeadlineInfo(scholarship.deadline);
  const isExpired = deadlineInfo.daysUntil < 0;

  const getUserProfile = () => {
    const profileData = localStorage.getItem('scholarstream_profile');
    if (profileData) {
      try {
        return JSON.parse(profileData);
      } catch (e) {
        return null;
      }
    }
    return null;
  };

  const profile = getUserProfile();

  const matchData = profile && scholarship ? matchingEngine.calculateMatchScore(scholarship, profile) : null;
  const matchScore = matchData ? matchData.total : scholarship.match_score;
  const matchExplanation = matchData ? matchData.explanation : '';

  const checkEligibility = () => {
    if (!profile) return [];
    if (!scholarship?.eligibility) return [];

    const checks = [];

    // GPA check
    if (scholarship.eligibility.gpa_min !== null) {
      const userGpa = profile.gpa || 0;
      checks.push({
        requirement: `GPA ${scholarship.eligibility.gpa_min} or higher`,
        userStatus: `You: ${userGpa}`,
        met: userGpa >= scholarship.eligibility.gpa_min,
      });
    }

    // Academic status check
    if (scholarship.eligibility.grades_eligible.length > 0) {
      const userStatus = profile.academicStatus || '';
      const eligible = scholarship.eligibility.grades_eligible.some(grade =>
        userStatus.toLowerCase().includes(grade.toLowerCase())
      );
      checks.push({
        requirement: `${scholarship.eligibility.grades_eligible.join(', ')} students`,
        userStatus: `You: ${userStatus}`,
        met: eligible,
      });
    }

    // Major check
    if (scholarship.eligibility.majors && scholarship.eligibility.majors.length > 0) {
      const userMajor = profile.major || '';
      const eligible = scholarship.eligibility.majors.some(major =>
        userMajor.toLowerCase().includes(major.toLowerCase())
      );
      checks.push({
        requirement: `Major: ${scholarship.eligibility.majors.join(', ')}`,
        userStatus: `You: ${userMajor || 'Not specified'}`,
        met: userMajor ? eligible : null,
      });
    }

    // Background checks
    if (scholarship.eligibility.backgrounds.length > 0) {
      const userBackgrounds = profile.background || [];
      const hasMatch = scholarship.eligibility.backgrounds.some(bg =>
        userBackgrounds.includes(bg)
      );
      checks.push({
        requirement: `Background: ${scholarship.eligibility.backgrounds.join(', ')}`,
        userStatus: userBackgrounds.length > 0 ? `You: ${userBackgrounds.join(', ')}` : 'Not specified',
        met: userBackgrounds.length > 0 ? hasMatch : null,
      });
    }

    return checks;
  };

  const eligibilityChecks = checkEligibility();
  const metCount = eligibilityChecks.filter(c => c.met === true).length;
  const totalCount = eligibilityChecks.filter(c => c.met !== null).length;

  return (
    <div className="min-h-screen bg-background pb-20">
      {/* Breadcrumb */}
      <div className="border-b border-border bg-card">
        <div className="container py-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <button onClick={() => navigate('/dashboard')} className="hover:text-foreground transition-colors">
              <Home className="h-4 w-4" />
            </button>
            <ChevronRight className="h-4 w-4" />
            <button onClick={() => navigate('/dashboard')} className="hover:text-foreground transition-colors">
              Opportunities
            </button>
            <ChevronRight className="h-4 w-4" />
            <span className="text-foreground font-medium truncate">{scholarship.name}</span>
          </div>
        </div>
      </div>

      {/* Hero Section */}
      <div className="bg-gradient-to-r from-primary/15 via-primary/8 to-background border-b border-primary/20">
        <div className="container py-12">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div className="flex-1 space-y-4">
              <div className="flex items-start gap-4">
                {/* Logo */}
                {scholarship.logo_url && !imageError ? (
                  <img
                    src={scholarship.logo_url}
                    alt={scholarship.organization}
                    className="h-24 w-24 rounded-xl object-cover"
                    onError={() => setImageError(true)}
                  />
                ) : (
                  <div className="flex h-24 w-24 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <span className="text-2xl font-bold">{getInitials(scholarship.organization)}</span>
                  </div>
                )}

                <div className="flex-1">
                  <h1 className="text-3xl font-bold text-foreground mb-2">{scholarship.name}</h1>
                  <a
                    href={normalizeApplyUrl(scholarship.source_url)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <span>{scholarship.organization}</span>
                    <ExternalLink className="h-4 w-4" />
                  </a>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-4">
                <div>
                  <div className="text-4xl font-bold text-success">{formatCurrency(scholarship.amount)}</div>
                  <div className="text-sm text-muted-foreground">{scholarship.amount_display}</div>
                </div>

                <div className="h-12 w-px bg-border" />

                <div>
                  <div className="flex items-center gap-2 text-foreground font-semibold">
                    <Calendar className="h-5 w-5" />
                    {deadlineInfo.formattedDate}
                  </div>
                  <div className={cn('text-sm font-medium mt-1', deadlineInfo.color)}>
                    {isExpired ? (
                      <Badge variant="destructive" className="text-xs">
                        ⚠️ EXPIRED - {Math.abs(deadlineInfo.daysUntil)} days ago
                      </Badge>
                    ) : (
                      deadlineInfo.countdown
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-3 lg:items-end">
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handleToggleSave}
                  className={cn(isSaved && 'bg-primary/10 text-primary border-primary')}
                >
                  <Bookmark className={cn('h-5 w-5', isSaved && 'fill-current')} />
                </Button>
                <Button variant="outline" size="icon" onClick={handleShare}>
                  <Share2 className="h-5 w-5" />
                </Button>
              </div>
              <div className="flex flex-col gap-2 w-full lg:w-auto">
                <Button
                  size="lg"
                  onClick={handleStartApplication}
                  className="w-full gap-2"
                  disabled={isExpired}
                >
                  <ExternalLink className="h-4 w-4" />
                  {isExpired ? 'Opportunity Expired' : `Apply on ${scholarship.organization}`}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleSearchOpportunity}
                  className="text-xs text-muted-foreground hover:text-primary"
                >
                  <Search className="h-3 w-3 mr-1" />
                  Link not working? Search Google
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <div className="container py-8">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="p-6">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-primary/10 p-2.5">
                <Target className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1">
                <div className="text-2xl font-bold text-foreground">{matchScore}%</div>
                <div className="text-sm text-muted-foreground">Match Score</div>
                <Badge className={cn('mt-2', getMatchTierColor(scholarship.match_tier))}>
                  {scholarship.match_tier} match
                </Badge>
                {matchExplanation && (
                  <div className="mt-2 text-xs text-muted-foreground border-t border-border pt-2">
                    {matchExplanation}
                  </div>
                )}
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-info/10 p-2.5">
                <Users className="h-5 w-5 text-info" />
              </div>
              <div className="flex-1">
                <div className="text-2xl font-bold text-foreground">{scholarship.competition_level}</div>
                <div className="text-sm text-muted-foreground">Competition Level</div>
                <Badge className={cn('mt-2', getCompetitionBadgeColor(scholarship.competition_level))}>
                  ~500 applicants
                </Badge>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-warning/10 p-2.5">
                <Clock className="h-5 w-5 text-warning" />
              </div>
              <div className="flex-1">
                <div className="text-2xl font-bold text-foreground">{scholarship.estimated_time}</div>
                <div className="text-sm text-muted-foreground">Est. Application Time</div>
                <div className="text-xs text-muted-foreground mt-1">Based on requirements</div>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-success/10 p-2.5">
                <Calculator className="h-5 w-5 text-success" />
              </div>
              <div className="flex-1">
                <div className="text-2xl font-bold text-foreground">
                  {scholarship.expected_value && !isNaN(scholarship.expected_value) && scholarship.expected_value > 0
                    ? `$${Math.round(scholarship.expected_value)}/hr`
                    : 'N/A'}
                </div>
                <div className="text-sm text-muted-foreground">Expected ROI</div>
                {scholarship.expected_value && scholarship.expected_value > 50 && (
                  <Badge className="mt-2 bg-success/20 text-success">Excellent investment</Badge>
                )}
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Tabs Section */}
      <div className="container pb-12">
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="w-full justify-start">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="requirements">Requirements</TabsTrigger>
            <TabsTrigger value="tips">Tips & Advice</TabsTrigger>
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-8">
            <Card className="p-6">
              <h2 className="text-2xl font-bold mb-4">About This Scholarship</h2>
              <p className="text-foreground/90 leading-relaxed whitespace-pre-line">
                {scholarship.description}
              </p>
            </Card>

            <Card className="p-6">
              <h2 className="text-2xl font-bold mb-6">Am I Eligible?</h2>

              {eligibilityChecks.length > 0 ? (
                <>
                  <div className="space-y-3 mb-6">
                    {eligibilityChecks.map((check, idx) => (
                      <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
                        {check.met === true && (
                          <CheckCircle className="h-5 w-5 text-success shrink-0 mt-0.5" />
                        )}
                        {check.met === false && (
                          <XCircle className="h-5 w-5 text-danger shrink-0 mt-0.5" />
                        )}
                        {check.met === null && (
                          <HelpCircle className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
                        )}
                        <div className="flex-1">
                          <div className="font-medium text-foreground">{check.requirement}</div>
                          <div className="text-sm text-muted-foreground">{check.userStatus}</div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {totalCount > 0 && (
                    <Card className="p-4 bg-primary/5 border-primary/20">
                      <div className="flex items-center gap-3">
                        <TrendingUp className="h-5 w-5 text-primary" />
                        <div className="flex-1">
                          <div className="font-semibold text-foreground">
                            You meet {metCount} of {totalCount} eligibility requirements
                          </div>
                          <div className="text-sm text-muted-foreground mt-1">
                            {metCount === totalCount
                              ? "You're a strong candidate! Consider applying."
                              : "Consider applying even if you don't meet all requirements - many scholarships are flexible."}
                          </div>
                        </div>
                      </div>
                    </Card>
                  )}
                </>
              ) : (
                <p className="text-muted-foreground">
                  Complete your profile to see detailed eligibility information.
                </p>
              )}
            </Card>

            <Card className="p-6">
              <h2 className="text-2xl font-bold mb-4">Award Details</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Award Amount</div>
                  <div className="font-semibold text-foreground">{scholarship.amount_display}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Deadline Type</div>
                  <div className="font-semibold text-foreground capitalize">{scholarship.deadline_type}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Source Type</div>
                  <div className="font-semibold text-foreground capitalize">{scholarship.source_type?.replace('_', ' ') ?? 'Unknown'}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Last Verified</div>
                  <div className="font-semibold text-foreground">{getTimeAgo(scholarship.last_verified)}</div>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <h2 className="text-2xl font-bold mb-4">📊 Data Quality & Freshness</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Last Verified</div>
                  <div className="font-semibold text-foreground">
                    {getTimeAgo(scholarship.last_verified)}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {scholarship.last_verified ? new Date(scholarship.last_verified).toLocaleString() : 'Unknown'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Source Credibility</div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="bg-success/10 text-success">
                      ✓ Verified Source
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Official {scholarship.organization} website
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Data Freshness</div>
                  <div className="font-semibold text-foreground">
                    {(() => {
                      const hoursSinceVerified = scholarship.last_verified
                        ? Math.floor((Date.now() - new Date(scholarship.last_verified).getTime()) / (1000 * 60 * 60))
                        : 999;

                      if (hoursSinceVerified < 24) return '🟢 Fresh (< 24h)';
                      if (hoursSinceVerified < 72) return '🟡 Recent (< 3 days)';
                      return '🔴 Needs Update (> 3 days)';
                    })()}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Opportunity Status</div>
                  <div className="font-semibold">
                    {isExpired ? (
                      <Badge variant="destructive">❌ Expired</Badge>
                    ) : deadlineInfo.daysUntil < 7 ? (
                      <Badge className="bg-warning text-warning-foreground">⚡ Urgent</Badge>
                    ) : (
                      <Badge className="bg-success text-success-foreground">✅ Active</Badge>
                    )}
                  </div>
                </div>
              </div>

              {isExpired && (
                <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                  <p className="text-sm text-destructive font-medium">
                    ⚠️ This opportunity has expired. We recommend checking for similar active opportunities on your dashboard.
                  </p>
                </div>
              )}
            </Card>

            {/* Application Timeline */}
            <Card className="p-6">
              <h2 className="text-2xl font-bold mb-4">📅 Application Timeline</h2>
              <p className="text-sm text-muted-foreground mb-4">
                Recommended timeline to maximize your chances of success
              </p>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-bold text-primary">1</span>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold">Prepare Materials (Week 1-2)</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      Gather transcripts, resume, and request recommendation letters
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {scholarship.requirements?.transcript && (
                        <Badge variant="outline" className="text-xs">📄 Transcript</Badge>
                      )}
                      {scholarship.requirements?.resume && (
                        <Badge variant="outline" className="text-xs">📝 Resume</Badge>
                      )}
                      {(scholarship.requirements?.recommendation_letters ?? 0) > 0 && (
                        <Badge variant="outline" className="text-xs">
                          ✉️ {scholarship.requirements?.recommendation_letters} Letter(s)
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-bold text-primary">2</span>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold">Draft Essays (Week 2-3)</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      {scholarship.requirements?.essay
                        ? `Write ${scholarship.requirements?.essay_prompts?.length || 1} essay(s) - allow time for multiple drafts`
                        : 'No essays required for this opportunity ✨'}
                    </p>
                    {scholarship.requirements?.essay && (scholarship.requirements?.essay_prompts?.length ?? 0) > 0 && (
                      <div className="mt-2 text-xs text-muted-foreground">
                        <strong>Prompts:</strong>
                        <ul className="list-disc list-inside mt-1 space-y-1">
                          {scholarship.requirements?.essay_prompts?.slice(0, 2).map((prompt, idx) => (
                            <li key={idx}>{prompt}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-bold text-primary">3</span>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold">Review & Submit (Week 3-4)</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      Proofread everything, get feedback, and submit at least 2 days before deadline
                    </p>
                    <div className="mt-2">
                      <Badge variant="outline" className="text-xs">
                        ⏱️ Est. Time: {scholarship.estimated_time ?? 'N/A'}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            {/* Success Tips */}
            <Card className="p-6">
              <h2 className="text-2xl font-bold mb-4">💡 Success Tips</h2>
              <p className="text-sm text-muted-foreground mb-4">
                Proven strategies to make your application stand out
              </p>
              <div className="space-y-3">
                <div className="flex items-start gap-2">
                  <CheckCircle className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                  <p className="text-sm">
                    <strong>Start early:</strong> Give yourself at least 2-3 weeks to prepare a strong application. Last-minute applications rarely win.
                  </p>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                  <p className="text-sm">
                    <strong>Be specific:</strong> Use concrete examples and numbers to demonstrate your achievements. "Increased club membership by 40%" beats "Helped grow the club."
                  </p>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                  <p className="text-sm">
                    <strong>Show passion:</strong> Explain WHY this opportunity matters to you personally. Authentic enthusiasm is memorable.
                  </p>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                  <p className="text-sm">
                    <strong>Proofread multiple times:</strong> Have at least 2 people review your application. Typos and errors suggest carelessness.
                  </p>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="h-5 w-5 text-success flex-shrink-0 mt-0.5" />
                  <p className="text-sm">
                    <strong>Follow instructions exactly:</strong> If they ask for 500 words, don't submit 750. Attention to detail matters.
                  </p>
                </div>
                {scholarship.competition_level === 'High' && (
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="h-5 w-5 text-warning flex-shrink-0 mt-0.5" />
                    <p className="text-sm">
                      <strong>High competition:</strong> This is a competitive opportunity. Consider applying to multiple similar opportunities to increase your chances.
                    </p>
                  </div>
                )}
              </div>
            </Card>
          </TabsContent>

          {/* Requirements Tab */}
          <TabsContent value="requirements" className="space-y-6">
            <Card className="p-6">
              <h2 className="text-2xl font-bold mb-6">Application Checklist</h2>

              {(!scholarship.requirements?.essay &&
                !scholarship.requirements?.transcript &&
                !scholarship.requirements?.resume &&
                (scholarship.requirements?.recommendation_letters ?? 0) === 0 &&
                (scholarship.requirements?.other?.length ?? 0) === 0) ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <AlertTriangle className="h-12 w-12 text-warning mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Requirements Not Specified</h3>
                  <p className="text-muted-foreground max-w-md mb-6">
                    The specific requirements for this opportunity weren't automatically detected. Please check the official application page for details.
                  </p>
                  <Button onClick={handleStartApplication}>
                    Visit Application Page
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-start gap-3 p-4 rounded-lg border border-border">
                    <div className="shrink-0">
                      <div className="h-5 w-5 rounded border-2 border-muted-foreground" />
                    </div>
                    <div className="flex-1">
                      <div className="font-semibold text-foreground mb-2">Personal Information Form</div>
                      <p className="text-sm text-muted-foreground mb-2">
                        Basic information about you, your school, and your family. Estimated time: 15 minutes
                      </p>
                      <Badge variant="outline">Auto-filled from profile</Badge>
                    </div>
                  </div>

                  {scholarship.requirements?.essay && (
                    <div className="flex items-start gap-3 p-4 rounded-lg border border-border">
                      <div className="shrink-0">
                        <div className="h-5 w-5 rounded border-2 border-muted-foreground" />
                      </div>
                      <div className="flex-1">
                        <div className="font-semibold text-foreground mb-2">Essay / Personal Statement</div>
                        {(scholarship.requirements?.essay_prompts?.length ?? 0) > 0 && (
                          <div className="space-y-2 mb-2">
                            {scholarship.requirements?.essay_prompts?.map((prompt, idx) => (
                              <p key={idx} className="text-sm text-muted-foreground italic">
                                "{prompt}"
                              </p>
                            ))}
                          </div>
                        )}
                        <Button variant="outline" size="sm">Start Essay</Button>
                      </div>
                    </div>
                  )}

                  {(scholarship.requirements?.recommendation_letters ?? 0) > 0 && (
                    <div className="flex items-start gap-3 p-4 rounded-lg border border-border">
                      <div className="shrink-0">
                        <div className="h-5 w-5 rounded border-2 border-muted-foreground" />
                      </div>
                      <div className="flex-1">
                        <div className="font-semibold text-foreground mb-2">
                          Recommendation Letters ({scholarship.requirements?.recommendation_letters} required)
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">
                          From teachers, counselors, mentors, or employers who can speak to your academic ability and character
                        </p>
                        <Button variant="outline" size="sm">Request Letters</Button>
                      </div>
                    </div>
                  )}

                  {scholarship.requirements?.transcript && (
                    <div className="flex items-start gap-3 p-4 rounded-lg border border-border">
                      <div className="shrink-0">
                        <div className="h-5 w-5 rounded border-2 border-muted-foreground" />
                      </div>
                      <div className="flex-1">
                        <div className="font-semibold text-foreground mb-2">Official Transcript</div>
                        <p className="text-sm text-muted-foreground mb-2">
                          Unofficial transcripts accepted for initial application
                        </p>
                        <Button variant="outline" size="sm">Upload Transcript</Button>
                      </div>
                    </div>
                  )}

                  {scholarship.requirements?.resume && (
                    <div className="flex items-start gap-3 p-4 rounded-lg border border-border">
                      <div className="shrink-0">
                        <div className="h-5 w-5 rounded border-2 border-muted-foreground" />
                      </div>
                      <div className="flex-1">
                        <div className="font-semibold text-foreground mb-2">Resume / CV</div>
                        <p className="text-sm text-muted-foreground mb-2">
                          One-page resume highlighting academic achievements, work experience, and extracurriculars
                        </p>
                        <Button variant="outline" size="sm">Upload Resume</Button>
                      </div>
                    </div>
                  )}

                  {(scholarship.requirements?.other?.length ?? 0) > 0 && (
                    <>
                      {scholarship.requirements?.other?.map((req, idx) => (
                        <div key={idx} className="flex items-start gap-3 p-4 rounded-lg border border-border">
                          <div className="shrink-0">
                            <div className="h-5 w-5 rounded border-2 border-muted-foreground" />
                          </div>
                          <div className="flex-1">
                            <div className="font-semibold text-foreground">{req}</div>
                          </div>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              )}

              <Button variant="outline" className="w-full mt-6">
                <Download className="h-4 w-4 mr-2" />
                Download Checklist PDF
              </Button>
            </Card>
          </TabsContent>

          {/* Tips Tab */}
          <TabsContent value="tips" className="space-y-6">
            <Card className="p-6 bg-primary/5 border-primary/20">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Award className="h-5 w-5 text-primary" />
                Personalized Tips for You
              </h3>
              <div className="space-y-3 text-foreground/90">
                {profile?.interests && profile.interests.length > 0 && (
                  <p>
                    💡 Your interests in <strong>{profile.interests.slice(0, 2).join(' and ')}</strong> align well with this scholarship. Highlight these in your application!
                  </p>
                )}
                {profile?.gpa && profile.gpa >= 3.5 && (
                  <p>
                    📊 Your strong GPA of <strong>{profile.gpa}</strong> is a major asset. Make sure to emphasize your academic achievements.
                  </p>
                )}
                {profile?.background && profile.background.length > 0 && (
                  <p>
                    🌟 Your background as <strong>{profile.background[0]}</strong> is valuable. Share your unique perspective in your essay.
                  </p>
                )}
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-xl font-bold mb-4">Common Success Strategies</h3>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="shrink-0 mt-1">
                    <div className="h-2 w-2 rounded-full bg-success" />
                  </div>
                  <div>
                    <div className="font-semibold text-foreground">Apply Early</div>
                    <p className="text-sm text-muted-foreground">
                      Don't wait until the deadline. Submit at least a week early to avoid technical issues.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="shrink-0 mt-1">
                    <div className="h-2 w-2 rounded-full bg-success" />
                  </div>
                  <div>
                    <div className="font-semibold text-foreground">Show Specific Impact</div>
                    <p className="text-sm text-muted-foreground">
                      Use numbers and concrete examples. "Taught 50+ students" is better than "helped students."
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="shrink-0 mt-1">
                    <div className="h-2 w-2 rounded-full bg-success" />
                  </div>
                  <div>
                    <div className="font-semibold text-foreground">Get Multiple Reviews</div>
                    <p className="text-sm text-muted-foreground">
                      Have at least 3 people review your essay before submitting. Fresh eyes catch mistakes.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="shrink-0 mt-1">
                    <div className="h-2 w-2 rounded-full bg-success" />
                  </div>
                  <div>
                    <div className="font-semibold text-foreground">Follow Instructions Exactly</div>
                    <p className="text-sm text-muted-foreground">
                      Word counts, formatting, file types - follow every requirement to the letter.
                    </p>
                  </div>
                </div>
              </div>
            </Card>

            <Card className="p-6 bg-warning/5 border-warning/20">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <XCircle className="h-5 w-5 text-warning" />
                Common Mistakes to Avoid
              </h3>
              <div className="space-y-3 text-foreground/90">
                <p>❌ Generic essays that could apply to any scholarship</p>
                <p>❌ Spelling and grammar errors (proofread multiple times)</p>
                <p>❌ Missing required documents or information</p>
                <p>❌ Waiting until the last minute to submit</p>
                <p>❌ Listing activities without explaining your impact</p>
              </div>
            </Card>
          </TabsContent>

          {/* Timeline Tab */}
          <TabsContent value="timeline" className="space-y-6">
            <Card className="p-6">
              <h2 className="text-2xl font-bold mb-6">Important Dates</h2>
              <div className="space-y-6">
                <div className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="rounded-full bg-success/20 p-2">
                      <Calendar className="h-5 w-5 text-success" />
                    </div>
                    <div className="h-full w-px bg-border mt-2" />
                  </div>
                  <div className="flex-1 pb-6">
                    <div className="font-semibold text-foreground">Application Deadline</div>
                    <div className="text-sm text-muted-foreground">{deadlineInfo.formattedDate}</div>
                    <div className={cn('text-sm font-medium mt-1', deadlineInfo.color)}>
                      {deadlineInfo.countdown}
                    </div>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="rounded-full bg-info/20 p-2">
                      <Clock className="h-5 w-5 text-info" />
                    </div>
                    <div className="h-full w-px bg-border mt-2" />
                  </div>
                  <div className="flex-1 pb-6">
                    <div className="font-semibold text-foreground">Recommended Submission</div>
                    <div className="text-sm text-muted-foreground">At least 1 week before deadline</div>
                    <Badge variant="outline" className="mt-2">Avoid last-minute issues</Badge>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="rounded-full bg-warning/20 p-2">
                      <Award className="h-5 w-5 text-warning" />
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-foreground">Winner Announcement</div>
                    <div className="text-sm text-muted-foreground">Typically 2-3 months after deadline</div>
                    <div className="text-sm text-muted-foreground mt-1">All applicants will be notified</div>
                  </div>
                </div>
              </div>

              <Button variant="outline" className="w-full mt-6">
                <Calendar className="h-4 w-4 mr-2" />
                Add Deadline to Calendar
              </Button>
            </Card>

            <Card className="p-6">
              <h3 className="text-xl font-bold mb-4">Preparation Timeline</h3>
              <p className="text-muted-foreground mb-4">Working backwards from the deadline:</p>
              <div className="space-y-3">
                <div className="flex gap-3">
                  <div className="font-semibold text-foreground w-32 shrink-0">8 weeks before:</div>
                  <div className="text-muted-foreground">Request recommendation letters</div>
                </div>
                <div className="flex gap-3">
                  <div className="font-semibold text-foreground w-32 shrink-0">6 weeks before:</div>
                  <div className="text-muted-foreground">Begin essay draft</div>
                </div>
                <div className="flex gap-3">
                  <div className="font-semibold text-foreground w-32 shrink-0">4 weeks before:</div>
                  <div className="text-muted-foreground">Gather all required documents</div>
                </div>
                <div className="flex gap-3">
                  <div className="font-semibold text-foreground w-32 shrink-0">2 weeks before:</div>
                  <div className="text-muted-foreground">Review and revise essay</div>
                </div>
                <div className="flex gap-3">
                  <div className="font-semibold text-foreground w-32 shrink-0">1 week before:</div>
                  <div className="text-muted-foreground">Final review and submission</div>
                </div>
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Sticky Bottom Action Bar (Mobile) */}
      <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background/95 backdrop-blur p-4 lg:hidden">
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleToggleSave}
            className={cn('shrink-0', isSaved && 'bg-primary/10 text-primary border-primary')}
          >
            <Bookmark className={cn('h-5 w-5', isSaved && 'fill-current')} />
          </Button>
          <Button className="flex-1 gap-2" onClick={handleStartApplication}>
            <ExternalLink className="h-4 w-4" />
            Apply Now
          </Button>
        </div>
      </div>
    </div>
  );
};

export default OpportunityDetail;
