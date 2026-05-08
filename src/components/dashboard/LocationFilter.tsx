import { useState, useMemo } from 'react';
import { MapPin, Globe, ChevronDown, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export type LocationScope = 'all' | 'local' | 'regional' | 'national' | 'international';

interface LocationFilterProps {
  userCountry?: string;
  userState?: string;
  selectedScope: LocationScope;
  onScopeChange: (scope: LocationScope) => void;
}

const scopeOptions: { value: LocationScope; label: string; description: string; icon: React.ReactNode }[] = [
  {
    value: 'all',
    label: 'All Opportunities',
    description: 'Show everything regardless of location',
    icon: <Globe className="h-4 w-4" />,
  },
  {
    value: 'local',
    label: 'Local First',
    description: 'Prioritize opportunities in your state/city',
    icon: <MapPin className="h-4 w-4" />,
  },
  {
    value: 'regional',
    label: 'Regional',
    description: 'Your country and neighboring regions',
    icon: <MapPin className="h-4 w-4" />,
  },
  {
    value: 'national',
    label: 'National',
    description: 'Opportunities within your country only',
    icon: <MapPin className="h-4 w-4" />,
  },
  {
    value: 'international',
    label: 'International',
    description: 'Global opportunities for ambitious students',
    icon: <Globe className="h-4 w-4" />,
  },
];

export { scopeOptions };

export const LocationFilter = ({
  userCountry,
  userState,
  selectedScope,
  onScopeChange,
}: LocationFilterProps) => {
  const [open, setOpen] = useState(false);

  const selectedOption = scopeOptions.find(opt => opt.value === selectedScope);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={cn(
            'gap-2 h-9',
            selectedScope !== 'all' && 'border-primary text-primary'
          )}
        >
          <MapPin className="h-4 w-4" />
          <span className="hidden sm:inline">
            {selectedOption?.label || 'Location'}
          </span>
          <ChevronDown className="h-3 w-3 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-72 p-2" align="start">
        <div className="space-y-1">
          {userCountry && (
            <div className="px-2 py-1.5 mb-2 text-xs text-muted-foreground border-b border-border">
              Your location: {userState ? `${userState}, ` : ''}{userCountry}
            </div>
          )}

          {scopeOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => {
                onScopeChange(option.value);
                setOpen(false);
              }}
              className={cn(
                'w-full flex items-start gap-3 p-2 rounded-md text-left transition-colors',
                selectedScope === option.value
                  ? 'bg-primary/10 text-primary'
                  : 'hover:bg-muted'
              )}
            >
              <div className="mt-0.5">{option.icon}</div>
              <div className="flex-1">
                <div className="font-medium text-sm">{option.label}</div>
                <div className="text-xs text-muted-foreground">
                  {option.description}
                </div>
              </div>
            </button>
          ))}
        </div>

        {selectedScope !== 'all' && (
          <Button
            variant="ghost"
            size="sm"
            className="w-full mt-2 text-xs"
            onClick={() => {
              onScopeChange('all');
              setOpen(false);
            }}
          >
            <X className="h-3 w-3 mr-1" />
            Clear Filter
          </Button>
        )}
      </PopoverContent>
    </Popover>
  );
};

// Utility function to filter opportunities by location scope
export const filterByLocation = <T extends { eligibility?: { states?: string[] | null; citizenship?: string | null }; geo_tags?: string[] }>(
  opportunities: T[],
  scope: LocationScope,
  userCountry?: string,
  userState?: string
): T[] => {
  if (scope === 'all') return opportunities;

  return opportunities.filter(opp => {
    // Standardize inputs
    const states = (opp.eligibility?.states || []).map(s => s.toLowerCase());
    const citizenship = (opp.eligibility?.citizenship || '').toLowerCase();
    const geoTags = (opp.geo_tags || []).map(t => t.toLowerCase());

    // Check for Global indicators
    const isGlobal =
      geoTags.includes('global') ||
      geoTags.includes('international') ||
      geoTags.includes('remote') ||
      citizenship.includes('international') ||
      citizenship.includes('any');

    switch (scope) {
      case 'local':
        // Prioritize local: show local opportunities matching state
        if (userState && states.length > 0) {
          return states.some(s => s.includes(userState.toLowerCase()));
        }
        // If strict local is requested but no state match, fallback is strict (don't show global)
        return false;

      case 'regional':
      case 'national':
        // Show if matches country OR is global
        if (userCountry) {
          const countryMatch =
            citizenship.includes(userCountry.toLowerCase()) ||
            geoTags.includes(userCountry.toLowerCase());

          return countryMatch || isGlobal;
        }
        return isGlobal;

      case 'international':
        // Show ONLY global/international
        return isGlobal;

      default:
        return true;
    }
  });
};

// Sorting function to prioritize by location relevance
export const sortByLocationRelevance = <T extends { eligibility?: { states?: string[] | null; citizenship?: string | null } }>(
  opportunities: T[],
  userCountry?: string,
  userState?: string
): T[] => {
  if (!userCountry && !userState) return opportunities;

  return [...opportunities].sort((a, b) => {
    const scoreA = getLocationRelevanceScore(a, userCountry, userState);
    const scoreB = getLocationRelevanceScore(b, userCountry, userState);
    return scoreB - scoreA; // Higher score first
  });
};

const getLocationRelevanceScore = (
  opp: { eligibility?: { states?: string[] | null; citizenship?: string | null } },
  userCountry?: string,
  userState?: string
): number => {
  let score = 0;
  const states = opp.eligibility?.states || [];
  const citizenship = opp.eligibility?.citizenship || '';

  // Local state match = highest priority
  if (userState && states.length > 0 && states.some(s => s.toLowerCase().includes(userState.toLowerCase()))) {
    score += 100;
  }

  // National match
  if (userCountry && (citizenship === '' || citizenship === null || citizenship.toLowerCase().includes(userCountry.toLowerCase()))) {
    score += 50;
  }

  // International opportunities are still valuable
  if (citizenship === '' || citizenship === null || citizenship.toLowerCase().includes('international') || citizenship.toLowerCase().includes('any')) {
    score += 25;
  }

  return score;
};
