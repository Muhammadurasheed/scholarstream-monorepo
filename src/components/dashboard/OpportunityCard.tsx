
import { useState, useMemo } from 'react';
import {
  Calendar,
  Clock,
  Bookmark,
  ExternalLink,
  MapPin,
  Trophy,
  Zap,
  TrendingUp,
  Users,
  DollarSign
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Scholarship, UserProfile } from '@/types/scholarship';
import {
  formatCurrency,
  getDeadlineInfo,
  isNewScholarship,
  normalizeApplyUrl,
} from '@/utils/scholarshipUtils';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';
import { matchingEngine } from '@/services/matchingEngine';

interface OpportunityCardProps {
  scholarship: Scholarship;
  isSaved: boolean;
  onToggleSave: (id: string) => void;
  onStartApplication: (id: string) => void;
  isJustAdded?: boolean;
}

// Type badge configuration
const TYPE_CONFIG = {
  scholarship: { label: 'Scholarship', color: 'bg-blue-500/10 text-blue-600 border-blue-500/20', icon: Trophy },
  hackathon: { label: 'Hackathon', color: 'bg-purple-500/10 text-purple-600 border-purple-500/20', icon: Zap },
  bounty: { label: 'Bounty', color: 'bg-orange-500/10 text-orange-600 border-orange-500/20', icon: DollarSign },
  competition: { label: 'Competition', color: 'bg-green-500/10 text-green-600 border-green-500/20', icon: TrendingUp },
};

// Source configuration for distinct branding - High Contrast V2
const SOURCE_CONFIG: Record<string, { label: string, color: string, icon?: string }> = {
  'devpost.com': { label: 'DevPost', color: 'bg-[#003E54] text-white border-transparent shadow-sm' },
  'dorahacks.io': { label: 'DoraHacks', color: 'bg-[#FF761C] text-white border-transparent shadow-sm' },
  'hackquest.io': { label: 'HackQuest', color: 'bg-indigo-600 text-white border-transparent shadow-sm' },
  'scholarships.com': { label: 'Scholarships.com', color: 'bg-blue-600 text-white border-transparent shadow-sm' },
  'bold.org': { label: 'Bold.org', color: 'bg-black text-white border-transparent shadow-sm' },
  'mlh.io': { label: 'MLH', color: 'bg-red-600 text-white border-transparent shadow-sm' },
  'hackerone.com': { label: 'HackerOne', color: 'bg-slate-800 text-white border-transparent shadow-sm' },
  'immunefi.com': { label: 'Immunefi', color: 'bg-purple-700 text-white border-transparent shadow-sm' },
  'kaggle.com': { label: 'Kaggle', color: 'bg-cyan-600 text-white border-transparent shadow-sm' },
};

// Match score color gradient
const getMatchScoreColor = (score: number) => {
  if (score >= 90) return 'text-green-500';
  if (score >= 75) return 'text-emerald-500';
  if (score >= 60) return 'text-yellow-500';
  if (score >= 40) return 'text-orange-500';
  return 'text-muted-foreground';
};

const getMatchScoreBg = (score: number) => {
  if (score >= 90) return 'bg-green-500/10 border-green-500/30';
  if (score >= 75) return 'bg-emerald-500/10 border-emerald-500/30';
  if (score >= 60) return 'bg-yellow-500/10 border-yellow-500/30';
  if (score >= 40) return 'bg-orange-500/10 border-orange-500/30';
  return 'bg-muted/50 border-border';
};

export const OpportunityCard = ({
  scholarship,
  isSaved,
  onToggleSave,
  onStartApplication,
  isJustAdded = false,
}: OpportunityCardProps) => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [imageError, setImageError] = useState(false);
  const deadlineInfo = getDeadlineInfo(scholarship.deadline);
  const isNew = isNewScholarship(scholarship.discovered_at);
  const showNewBanner = isJustAdded || isNew;

  // Calculate match score - ALWAYS recalculate to fix 47% ghost issue
  const matchScore = useMemo(() => {
    // Always calculate fresh score using matchingEngine
    try {
      const profileData = localStorage.getItem('scholarstream_profile');
      if (profileData) {
        const profile = JSON.parse(profileData) as UserProfile;
        const matchData = matchingEngine.calculateMatchScore(scholarship, profile);
        // Only use stored score if calculated score is 0 (indicates error)
        return matchData.total > 0 ? matchData.total : (scholarship.match_score || 50);
      }
    } catch {
      // Fall back to stored score
    }

    return scholarship.match_score || 50;
  }, [scholarship]);

  // Infer type from data
  const inferType = (): keyof typeof TYPE_CONFIG => {
    const tags = (scholarship.tags || []).map(t => t.toLowerCase()).join(' ');
    const name = (scholarship.name || '').toLowerCase();
    const desc = (scholarship.description || '').toLowerCase();
    const combined = `${tags} ${name} ${desc}`;

    if (combined.includes('hackathon') || combined.includes('devpost') || combined.includes('mlh')) return 'hackathon';
    if (combined.includes('bounty') || combined.includes('bug')) return 'bounty';
    if (combined.includes('competition') || combined.includes('contest') || combined.includes('kaggle')) return 'competition';
    return 'scholarship';
  };

  // Get Friendly Source
  const getSourceConfig = () => {
    if (!scholarship.source_url) return null;
    try {
      const hostname = new URL(scholarship.source_url).hostname.replace('www.', '');
      // Exact match
      if (SOURCE_CONFIG[hostname]) return SOURCE_CONFIG[hostname];

      // Partial match (e.g. subdomains)
      for (const key in SOURCE_CONFIG) {
        if (hostname.includes(key)) return SOURCE_CONFIG[key];
      }

      // Fallback
      return {
        label: hostname.split('.')[0].charAt(0).toUpperCase() + hostname.split('.')[0].slice(1),
        color: 'bg-secondary/50 text-muted-foreground border-border/50'
      };
    } catch (e) {
      return null;
    }
  };

  const opportunityType = inferType();
  const typeConfig = TYPE_CONFIG[opportunityType];
  const TypeIcon = typeConfig.icon;
  const sourceConfig = getSourceConfig();

  const getInitials = (name: string | null | undefined) => {
    if (!name) return '??';
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const handleApplyExternal = (e: React.MouseEvent) => {
    e.stopPropagation();
    onStartApplication(scholarship.id);

    // Smart fallback: try source_url, then navigate to details page
    if (scholarship.source_url) {
      const normalizedUrl = normalizeApplyUrl(scholarship.source_url);
      window.open(normalizedUrl, '_blank', 'noopener,noreferrer');
      toast({
        title: 'Application opened',
        description: 'Good luck with your application!',
      });
    } else {
      // Fallback: navigate to detail page with application instructions
      navigate(`/opportunity/${scholarship.id}`);
      toast({
        title: 'Opening details',
        description: 'Check the opportunity page for application link.',
      });
    }
  };

  const handleToggleSaveWrapper = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggleSave(scholarship.id);
  };

  // Helper to strip HTML tags from scraper data
  const stripHtml = (html: string) => {
    if (!html) return '';
    const tmp = document.createElement('DIV');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
  };

  // Format amount display -> Cleaned & Enhanced for DoraHacks/MLH
  const getDisplayAmount = (): string => {
    // Priority 1: Use numeric amount if > 0
    if (scholarship.amount > 0) {
      return formatCurrency(scholarship.amount);
    }
    
    // Priority 2: Use amount_display if it has value content
    const amountDisplay = stripHtml(scholarship.amount_display || '');
    if (amountDisplay && 
        !['varies', 'see details', 'tbd', 'n/a', 'unknown', '$0', '0'].includes(amountDisplay.toLowerCase().trim())) {
      return amountDisplay;
    }
    
    // Priority 3: Check tags for prize info (common in hackathons)
    const tags = scholarship.tags || [];
    const prizeTag = tags.find(t => t.toLowerCase().includes('prize') || t.toLowerCase().includes('$'));
    if (prizeTag) {
      return prizeTag;
    }
    
    // V2 FIX: Better call-to-action instead of generic text
    const type = inferType();
    if (type === 'hackathon' || type === 'bounty') {
      return 'View Prizes →';
    }
    return 'View Details →';
  };
  
  const displayAmount = getDisplayAmount();

  return (
    <Card
      className={cn(
        'group relative flex flex-col overflow-hidden transition-all duration-300',
        'hover:shadow-xl hover:-translate-y-1 cursor-pointer',
        'border border-border/50 bg-card'
      )}
      onClick={() => navigate(`/opportunity/${scholarship.id}`)}
    >
      {/* JUST ADDED Banner - Full width, very prominent */}
      {isJustAdded && (
        <div className="absolute inset-x-0 top-0 z-20">
          <div className="bg-gradient-to-r from-green-500 via-emerald-500 to-teal-500 text-white text-xs font-bold px-4 py-2 flex items-center justify-center gap-2 shadow-lg animate-pulse">
            <span className="text-base">🎉</span>
            <span>JUST ADDED</span>
            <span className="text-base">✨</span>
          </div>
        </div>
      )}

      {/* NEW Badge - Corner badge for 72-hour new items (not just added) */}
      {showNewBanner && !isJustAdded && (
        <div className="absolute -top-1 -right-1 z-20">
          <div className="relative">
            {/* Glow effect */}
            <div className="absolute inset-0 bg-primary rounded-full blur-md opacity-50 animate-pulse" />
            {/* Badge */}
            <div className="relative bg-gradient-to-r from-primary via-primary to-primary/90 text-primary-foreground text-[10px] font-bold px-3 py-1.5 rounded-full shadow-lg border-2 border-primary-foreground/20">
              ✨ NEW
            </div>
          </div>
        </div>
      )}

      {/* Top accent bar based on match score */}
      <div className={cn(
        'h-1 w-full',
        isJustAdded ? 'mt-8' : '', // Add margin when just added banner is shown
        matchScore >= 85 ? 'bg-gradient-to-r from-green-500 to-emerald-500' :
          matchScore >= 70 ? 'bg-gradient-to-r from-emerald-500 to-teal-500' :
            matchScore >= 50 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' :
              'bg-gradient-to-r from-muted to-muted-foreground/20'
      )} />

      <div className="p-5 flex flex-col flex-1">
        {/* Header Row: Type Badge + Source Badge (Replaces old badges) */}
        <div className="flex items-center justify-between mb-3 pr-8"> {/* Added pr-8 to avoid overlap with banner */}
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className={cn('text-xs font-medium', typeConfig.color)}>
              <TypeIcon className="w-3 h-3 mr-1" />
              {typeConfig.label}
            </Badge>

            {sourceConfig && (
              <Badge variant="outline" className={cn('text-[10px] px-2 py-0 border font-medium flex-shrink-0', sourceConfig.color)}>
                {sourceConfig.label}
              </Badge>
            )}
          </div>

          <Button
            size="sm"
            variant="ghost"
            className="h-8 w-8 p-0 opacity-60 hover:opacity-100"
            onClick={handleToggleSaveWrapper}
          >
            <Bookmark
              className={cn('h-4 w-4 transition-colors', isSaved && 'fill-primary text-primary')}
            />
          </Button>
        </div>

        {/* Organization + Logo Row */}
        <div className="flex items-start gap-3 mb-3">
          <div className="flex-shrink-0">
            {scholarship.logo_url && !imageError ? (
              <img
                src={scholarship.logo_url}
                alt={scholarship.organization}
                className="h-12 w-12 rounded-lg object-cover border border-border/50"
                onError={() => setImageError(true)}
              />
            ) : (
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary border border-primary/20">
                <span className="text-sm font-bold">{getInitials(scholarship.organization)}</span>
              </div>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-muted-foreground truncate mb-0.5">
              {scholarship.organization}
            </p>
            <h3 className="line-clamp-2 text-base font-semibold text-foreground leading-tight group-hover:text-primary transition-colors">
              {scholarship.name}
            </h3>
          </div>
        </div>

        {/* Amount - Prominent Display */}
        <div className="flex items-baseline gap-2 mb-4">
          <span className="text-sm font-medium text-slate-300">
            {Math.round(matchScore)}%
          </span>
          <span className="text-2xl font-bold text-success">
            {displayAmount}
          </span>
          {scholarship.amount > 0 && scholarship.amount_display &&
            scholarship.amount_display !== formatCurrency(scholarship.amount) && (
              <span className="text-xs text-muted-foreground">
                {scholarship.amount_display}
              </span>
            )}
        </div>

        {/* Deadline Row - Color coded urgency */}
        <div className={cn(
          'flex items-center gap-2 px-3 py-2 rounded-lg mb-4',
          deadlineInfo.daysUntil <= 7 ? 'bg-destructive/10 border border-destructive/20' :
            deadlineInfo.daysUntil <= 14 ? 'bg-orange-500/10 border border-orange-500/20' :
              deadlineInfo.daysUntil <= 30 ? 'bg-yellow-500/10 border border-yellow-500/20' :
                'bg-muted/50 border border-border/50'
        )}>
          <Calendar className={cn(
            'h-4 w-4 flex-shrink-0',
            deadlineInfo.daysUntil <= 7 ? 'text-destructive' :
              deadlineInfo.daysUntil <= 14 ? 'text-orange-500' :
                deadlineInfo.daysUntil <= 30 ? 'text-yellow-600' :
                  'text-muted-foreground'
          )} />
          <span className="text-sm font-medium">{deadlineInfo.formattedDate}</span>
          {deadlineInfo.daysUntil >= 0 && (
            <span className={cn('text-xs font-semibold ml-auto', deadlineInfo.color)}>
              {deadlineInfo.countdown}
            </span>
          )}
        </div>

        {/* Tags Row */}
        {(scholarship.tags || []).length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {(scholarship.tags || []).slice(0, 3).map((tag, index) => (
              <Badge key={index} variant="secondary" className="text-xs px-2 py-0.5 bg-secondary/50">
                {tag}
              </Badge>
            ))}
            {(scholarship.tags || []).length > 3 && (
              <Badge variant="secondary" className="text-xs px-2 py-0.5 bg-secondary/50">
                +{(scholarship.tags || []).length - 3}
              </Badge>
            )}
          </div>
        )}

        {/* Meta Info Row */}
        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground mb-4">
          {scholarship.eligibility?.states && scholarship.eligibility.states.length > 0 && (
            <div className="flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              <span className="truncate max-w-[80px]">
                {scholarship.eligibility.states[0]}
              </span>
            </div>
          )}
          {scholarship.estimated_time && (
            <div className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{scholarship.estimated_time}</span>
            </div>
          )}
          {scholarship.competition_level && (
            <div className="flex items-center gap-1">
              <Users className="h-3 w-3" />
              <span className="capitalize">{scholarship.competition_level}</span>
            </div>
          )}
        </div>

        {/* Spacer to push bottom content down */}
        <div className="flex-1" />

        {/* Match Score + Actions - Always at bottom */}
        <div className="pt-4 border-t border-border/50">
          {/* Match Score Display */}
          <div className={cn(
            'flex items-center justify-between px-3 py-2 rounded-lg mb-3 border',
            getMatchScoreBg(matchScore)
          )}>
            <span className="text-xs font-medium text-muted-foreground">Match Score</span>
            <div className="flex items-center gap-2">
              <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className={cn(
                    'h-full rounded-full transition-all duration-500',
                    matchScore >= 85 ? 'bg-green-500' :
                      matchScore >= 70 ? 'bg-emerald-500' :
                        matchScore >= 50 ? 'bg-yellow-500' :
                          'bg-orange-500'
                  )}
                  style={{ width: `${matchScore}%` }}
                />
              </div>
              <span className={cn('text-sm font-bold', getMatchScoreColor(matchScore))}>
                {Math.round(matchScore)}%
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              className="flex-1 text-xs h-9"
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/opportunity/${scholarship.id}`);
              }}
            >
              <ExternalLink className="mr-1.5 h-3.5 w-3.5" />
              Details
            </Button>
            <Button
              size="sm"
              className="flex-1 text-xs h-9 bg-primary hover:bg-primary/90"
              onClick={handleApplyExternal}
            >
              Apply Now
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
};
