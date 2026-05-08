import { useState, useMemo, useEffect } from 'react';
import { Bookmark, Search, Grid, List, Download } from 'lucide-react';
import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { ScholarshipCard } from '@/components/dashboard/ScholarshipCard';
import { OpportunityTypeFilter } from '@/components/dashboard/OpportunityTypeFilter';
import { FloatingChatAssistant } from '@/components/dashboard/FloatingChatAssistant';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useScholarships } from '@/hooks/useScholarships';
import { useAuth } from '@/contexts/AuthContext';
import { Skeleton } from '@/components/ui/skeleton';
import { sortScholarships } from '@/utils/scholarshipUtils';
import { SortOption, ViewMode } from '@/types/scholarship';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const SavedOpportunities = () => {
  const { user } = useAuth();
  const {
    scholarships,
    loading,
    savedScholarshipIds,
    toggleSaveScholarship,
    startApplication,
  } = useScholarships();

  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('best_match');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [opportunityType, setOpportunityType] = useState<string>('all');

  // Filter to only saved scholarships
  const savedScholarships = useMemo(() => {
    return scholarships.filter(s => savedScholarshipIds.has(s.id));
  }, [scholarships, savedScholarshipIds]);

  // Apply filters
  const filteredAndSortedScholarships = useMemo(() => {
    let filtered = [...savedScholarships];

    // Filter by opportunity type
    if (opportunityType !== 'all') {
      filtered = filtered.filter(s => s.source_type === opportunityType);
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        s =>
          s.name.toLowerCase().includes(query) ||
          s.organization.toLowerCase().includes(query) ||
          s.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    return sortScholarships(filtered, sortBy);
  }, [savedScholarships, searchQuery, sortBy, opportunityType]);

  // Calculate opportunity type counts
  const opportunityCounts = useMemo(() => {
    const counts = {
      all: savedScholarships.length,
      scholarship: savedScholarships.filter(s => s.source_type === 'platform' || s.source_type === 'government').length,
      hackathon: savedScholarships.filter(s => s.source_type === 'devpost').length,
      bounty: savedScholarships.filter(s => s.source_type === 'gitcoin').length,
      competition: savedScholarships.filter(s => s.source_type === 'kaggle').length,
      grant: savedScholarships.filter(s => s.source_type === 'government').length,
    };
    return counts;
  }, [savedScholarships]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <DashboardHeader />
        <div className="container py-8">
          <Skeleton className="h-24 w-full mb-8" />
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="h-64" />
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
          <div className="flex items-center gap-3 mb-2">
            <Bookmark className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold">Saved Opportunities</h1>
          </div>
          <p className="text-muted-foreground">
            {savedScholarships.length} opportunities saved for later
          </p>
        </div>

        {savedScholarships.length === 0 ? (
          <div className="text-center py-16">
            <Bookmark className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-2xl font-semibold mb-2">No saved opportunities yet</h2>
            <p className="text-muted-foreground mb-6">
              Browse opportunities and click the bookmark icon to save them for later
            </p>
            <Button onClick={() => (window.location.href = '/dashboard')}>
              Browse Opportunities
            </Button>
          </div>
        ) : (
          <>
            {/* Filters */}
            <div className="space-y-4 mb-8">
              <OpportunityTypeFilter
                selectedType={opportunityType}
                onTypeChange={setOpportunityType}
                counts={opportunityCounts}
              />

              <div className="flex flex-col sm:flex-row gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search saved opportunities..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>

                <div className="flex gap-2">
                  <Select value={sortBy} onValueChange={(value) => setSortBy(value as SortOption)}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="best_match">Best Match</SelectItem>
                      <SelectItem value="deadline">Deadline</SelectItem>
                      <SelectItem value="amount_high">Highest Amount</SelectItem>
                      <SelectItem value="amount_low">Lowest Amount</SelectItem>
                      <SelectItem value="newest">Recently Added</SelectItem>
                    </SelectContent>
                  </Select>

                  <div className="flex gap-1 border rounded-lg p-1">
                    <Button
                      variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
                      size="icon"
                      onClick={() => setViewMode('grid')}
                    >
                      <Grid className="h-4 w-4" />
                    </Button>
                    <Button
                      variant={viewMode === 'list' ? 'secondary' : 'ghost'}
                      size="icon"
                      onClick={() => setViewMode('list')}
                    >
                      <List className="h-4 w-4" />
                    </Button>
                  </div>

                  <Button variant="outline" size="icon">
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Opportunities Grid */}
            <div className={
              viewMode === 'grid'
                ? 'grid gap-6 sm:grid-cols-2 lg:grid-cols-3'
                : 'space-y-4'
            }>
              {filteredAndSortedScholarships.map((scholarship) => (
              <ScholarshipCard
                key={scholarship.id}
                scholarship={scholarship}
                isSaved={savedScholarshipIds.has(scholarship.id)}
                onToggleSave={() => toggleSaveScholarship(scholarship.id)}
                onStartApplication={() => startApplication(scholarship.id)}
              />
              ))}
            </div>

            {filteredAndSortedScholarships.length === 0 && searchQuery && (
              <div className="text-center py-16">
                <p className="text-muted-foreground">No saved opportunities match your search</p>
              </div>
            )}
          </>
        )}
      </main>

      <FloatingChatAssistant />
    </div>
  );
};

export default SavedOpportunities;
