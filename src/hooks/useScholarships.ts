import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Scholarship, DashboardStats, UserProfile } from '@/types/scholarship';
import { apiService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';

export const useScholarships = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Local state for discovery UI (since it's transient)
  const [discoveryStatus, setDiscoveryStatus] = useState<'idle' | 'processing' | 'completed'>('idle');
  const [discoveryProgress, setDiscoveryProgress] = useState(0);

  // 1. Main Query: Fetch Matched Scholarships
  const {
    data: matchedData,
    isLoading: loading,
    refetch: refreshScholarships
  } = useQuery({
    queryKey: ['scholarships', user?.uid],
    queryFn: async () => {
      if (!user?.uid) return { scholarships: [], total_value: 0, last_updated: '' };
      return apiService.getMatchedScholarships(user.uid);
    },
    enabled: !!user?.uid,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const scholarships = matchedData?.scholarships || [];
  const lastUpdated = matchedData?.last_updated || '';

  // Calculate base stats
  const stats: DashboardStats = {
    opportunities_matched: scholarships.length,
    total_value: scholarships.reduce((sum, s) => sum + (s.amount || 0), 0),
    urgent_deadlines: scholarships.filter(s => {
      if (!s.deadline) return false;
      const deadline = new Date(s.deadline);
      if (isNaN(deadline.getTime())) return false;
      const daysUntil = Math.floor((deadline.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
      return daysUntil < 7 && daysUntil >= 0;
    }).length,
    applications_started: 0,
  };

  // 2. Mutation: Save/Unsave Scholarship
  const toggleSaveMutation = useMutation({
    mutationFn: async ({ id, isSaved }: { id: string; isSaved: boolean }) => {
      if (!user?.uid) throw new Error('User not logged in');
      if (isSaved) {
        await apiService.unsaveScholarship(user.uid, id);
      } else {
        await apiService.saveScholarship(user.uid, id);
      }
    },
    onMutate: async ({ id, isSaved }) => {
      // Optimistic Update
      await queryClient.cancelQueries({ queryKey: ['savedScholarships', user?.uid] });
      const previousSaved = queryClient.getQueryData(['savedScholarships', user?.uid]);

      queryClient.setQueryData(['savedScholarships', user?.uid], (old: Set<string> | undefined) => {
        const newSet = new Set(old);
        if (isSaved) newSet.delete(id);
        else newSet.add(id);
        return newSet;
      });

      return { previousSaved };
    },
    onError: (err, newTodo, context) => {
      queryClient.setQueryData(['savedScholarships', user?.uid], context?.previousSaved);
      toast({
        variant: 'destructive',
        title: 'Action failed',
        description: 'Please try again.',
      });
    },
    onSuccess: (_, { isSaved }) => {
      toast({
        title: isSaved ? 'Removed from favorites' : 'Saved to favorites',
        description: isSaved ? 'Scholarship removed from your saved list.' : 'You can find this scholarship in your saved list.',
      });
    },
  });

  // 3. Query: Saved Scholarship IDs
  const { data: savedScholarshipIds = new Set<string>() } = useQuery({
    queryKey: ['savedScholarships', user?.uid],
    queryFn: async () => {
      // TODO: Add endpoint to get just saved IDs
      return new Set<string>();
    },
    enabled: !!user?.uid,
    initialData: new Set<string>(),
  });

  // 4. Discovery Logic
  const triggerDiscovery = useCallback(async (profileData: UserProfile) => {
    if (!user?.uid) return;

    try {
      setDiscoveryStatus('processing');
      setDiscoveryProgress(10);

      toast({
        title: '🔍 Discovering opportunities...',
        description: 'Searching scholarship databases, hackathons, and bounties...',
      });

      const response = await apiService.discoverScholarships(user.uid, profileData);

      // Update cache immediately with initial results
      if (response.immediate_results) {
        queryClient.setQueryData(['scholarships', user.uid], (old: any) => ({
          ...old,
          scholarships: response.immediate_results,
          total_value: response.immediate_results.reduce((sum: number, s: Scholarship) => sum + s.amount, 0),
        }));
        setDiscoveryProgress(50);
      }

      // Poll for completion
      if (response.job_id) {
        const pollInterval = setInterval(async () => {
          try {
            const status = await apiService.getDiscoveryProgress(response.job_id);
            setDiscoveryProgress(prev => Math.min(prev + 10, 90));

            if (status.new_scholarships && status.new_scholarships.length > 0) {
              queryClient.setQueryData(['scholarships', user.uid], (old: any) => ({
                ...old,
                scholarships: [...(old?.scholarships || []), ...status.new_scholarships],
              }));
            }

            if (status.status === 'completed') {
              clearInterval(pollInterval);
              setDiscoveryStatus('completed');
              setDiscoveryProgress(100);
              toast({
                title: '✅ Discovery complete!',
                description: 'Your personalized matches are ready.',
              });
              // Final refetch to ensure consistency
              queryClient.invalidateQueries({ queryKey: ['scholarships', user.uid] });
            }
          } catch (e) {
            clearInterval(pollInterval);
            setDiscoveryStatus('completed');
          }
        }, 2000);
      } else {
        setDiscoveryStatus('completed');
        setDiscoveryProgress(100);
      }

    } catch (error) {
      console.error('Discovery failed:', error);
      setDiscoveryStatus('idle');
      toast({
        variant: 'destructive',
        title: 'Discovery failed',
        description: 'Please try again later.',
      });
    }
  }, [user, queryClient, toast]);

  const toggleSaveScholarship = (id: string) => {
    toggleSaveMutation.mutate({ id, isSaved: savedScholarshipIds.has(id) });
  };

  const startApplication = async (scholarshipId: string) => {
    if (!user?.uid) return;
    try {
      await apiService.startApplication(user.uid, scholarshipId);
      toast({
        title: 'Application started',
        description: 'Your progress has been saved.',
      });
    } catch (error) {
      console.error('Failed to start application:', error);
    }
  };

  return {
    scholarships,
    stats,
    loading,
    discoveryStatus,
    discoveryProgress,
    savedScholarshipIds,
    toggleSaveScholarship,
    startApplication,
    refreshScholarships,
    triggerDiscovery,
  };
};