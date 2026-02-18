import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { OnboardingData } from '@/pages/Onboarding';
import { CheckCircle2, Sparkles, Loader2, TrendingUp, DollarSign } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { apiService } from '@/services/api';
import Confetti from 'react-confetti';

interface Step9Props {
  data: OnboardingData;
  onComplete: () => void;
}

const Step9Complete: React.FC<Step9Props> = ({ data, onComplete }) => {
  const [discoveryStats, setDiscoveryStats] = useState<{
    counts: { scholarships: number, hackathons: number, bounties: number, competitions: number },
    totalValue: number
  } | null>(null);
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadingMessage, setLoadingMessage] = useState('Analyzing your profile...');
  const [showConfetti, setShowConfetti] = useState(false);

  useEffect(() => {
    const initiateDiscovery = async () => {
      if (!user) return;

      const messages = [
        'Analyzing your profile...',
        'Searching across multiple opportunity databases...',
        'Running AI matching algorithm...',
        'Calculating match scores and priorities...',
        'Almost ready...',
      ];

      let messageIndex = 0;
      const interval = setInterval(() => {
        messageIndex++;
        if (messageIndex < messages.length) {
          setLoadingMessage(messages[messageIndex]);
        }
      }, 1200);

      try {
        const profile = {
          name: `${data.firstName} ${data.lastName}`,
          academic_status: data.academicStatus,
          year: data.year,
          school: data.school,
          gpa: data.gpa,
          major: data.major,
          graduation_year: data.graduationYear,
          background: data.background,
          financial_need: data.financialNeed,
          interests: data.interests,
          motivation: data.motivation,
          time_commitment: data.timeCommitment,
          availability: data.availability,
          country: data.country,
          state: data.state,
          city: data.city,
        };

        const response = await apiService.discoverScholarships(user.uid, profile);
        console.log("Discovery response:", response);

        // Process real results if available
        let foundScholarships = response.immediate_results || [];
        if (response.new_scholarships) {
          foundScholarships = [...foundScholarships, ...response.new_scholarships];
        }

        if (foundScholarships.length > 0) {
          const newCounts = { scholarships: 0, hackathons: 0, bounties: 0, competitions: 0 };
          let newVal = 0;

          foundScholarships.forEach(s => {
            newVal += s.amount || 0;


            if (s.source_url?.includes('devpost') || s.source_url?.includes('mlh')) newCounts.hackathons++;
            else if (s.source_url?.includes('gitcoin')) newCounts.bounties++;
            else if (s.source_url?.includes('kaggle')) newCounts.competitions++;
            else newCounts.scholarships++;
          });

          setDiscoveryStats({
            counts: newCounts,
            totalValue: newVal
          });
        }

        clearInterval(interval);
        setLoading(false);
        setShowConfetti(true);
        setTimeout(() => setShowConfetti(false), 5000);
      } catch (err: any) {
        console.error('Failed to initiate opportunity discovery:', err);
        clearInterval(interval);
        setLoading(false);
        setError('Discovery service temporarily unavailable. Your opportunities will be ready shortly.');
      }
    };

    initiateDiscovery();
  }, [user, data]);

  // Use real stats if available, otherwise show zeroes or null state (handled in render)
  const counts = discoveryStats?.counts || { scholarships: 0, hackathons: 0, bounties: 0, competitions: 0 };
  const totalValue = discoveryStats?.totalValue || 0;

  return (
    <div className="space-y-8 animate-fade-in text-center max-w-2xl mx-auto">
      {showConfetti && <Confetti recycle={false} numberOfPieces={500} />}

      {/* Success Icon */}
      <div className="relative py-8">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className={`h-32 w-32 rounded-full ${loading ? 'bg-primary/10 animate-pulse' : 'bg-success/10 animate-ping'}`}></div>
        </div>
        {loading ? (
          <Loader2 className="h-24 w-24 text-primary mx-auto relative z-10 animate-spin" />
        ) : (
          <CheckCircle2 className="h-24 w-24 text-success mx-auto relative z-10 animate-scale-in" />
        )}
      </div>

      <div className="space-y-4">
        <h1 className="text-4xl md:text-5xl font-bold text-foreground tracking-tight">
          {loading ? 'One moment...' : `You're all set, ${data.firstName}!`}
        </h1>
        {loading ? (
          <p className="text-xl text-muted-foreground animate-pulse font-medium">
            {loadingMessage}
          </p>
        ) : error ? (
          <p className="text-lg text-destructive font-semibold bg-destructive/10 py-2 px-4 rounded-full inline-block">
            ⚠️ {error}
          </p>
        ) : (
          <p className="text-xl text-success font-semibold flex items-center justify-center gap-2">
            <Sparkles className="h-5 w-5" />
            Profile complete! Your personalized opportunities are ready.
          </p>
        )}
      </div>

      {!loading && !error && (
        <div className="space-y-6 animate-fade-in">
          {/* Opportunity Breakdown */}
          <Card className="p-6 text-left border-2 border-primary/20 shadow-lg bg-gradient-to-br from-primary/5 to-transparent">
            {discoveryStats ? (
              <>
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  <h3 className="text-lg font-bold text-foreground">Based on your profile, here's what we found:</h3>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
                    <div className="text-2xl font-bold text-blue-600">{counts.scholarships}</div>
                    <div className="text-muted-foreground text-xs mt-1">Scholarships</div>
                  </div>
                  <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/20">
                    <div className="text-2xl font-bold text-purple-600">{counts.hackathons}</div>
                    <div className="text-muted-foreground text-xs mt-1">Hackathons</div>
                  </div>
                  <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/20">
                    <div className="text-2xl font-bold text-green-600">{counts.bounties}</div>
                    <div className="text-muted-foreground text-xs mt-1">Bounties</div>
                  </div>
                  <div className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/20">
                    <div className="text-2xl font-bold text-amber-600">{counts.competitions}</div>
                    <div className="text-muted-foreground text-xs mt-1">Competitions</div>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-success/10 border border-success/20 rounded-lg flex items-center justify-center gap-2">
                  <DollarSign className="h-5 w-5 text-success" />
                  <span className="font-bold text-lg text-success">Total potential value: ${totalValue.toLocaleString()}</span>
                </div>
              </>
            ) : (
              <div className="text-center py-6">
                <p className="text-lg font-semibold text-foreground">Searching for opportunities...</p>
                <p className="text-muted-foreground">Our AI agents are currently scouring the web for matched opportunities. They will appear on your dashboard shortly.</p>
              </div>
            )}
          </Card>

          {/* Profile Summary */}
          <Card className="p-6 text-left border border-border/50 shadow-sm bg-card">
            <h3 className="text-lg font-bold mb-4 text-foreground border-b border-border pb-2">Your Profile</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground block mb-1">Name</span>
                <span className="font-semibold text-foreground">{data.firstName} {data.lastName}</span>
              </div>
              <div>
                <span className="text-muted-foreground block mb-1">Academic Status</span>
                <span className="font-semibold text-foreground capitalize">
                  {data.academicStatus.replace('-', ' ')}
                  {data.year && ` (${data.year})`}
                </span>
              </div>
              {data.major && (
                <div>
                  <span className="text-muted-foreground block mb-1">Major</span>
                  <span className="font-semibold text-foreground">{data.major}</span>
                </div>
              )}
              {data.gpa && (
                <div>
                  <span className="text-muted-foreground block mb-1">GPA</span>
                  <span className="font-semibold text-foreground">{data.gpa.toFixed(1)}</span>
                </div>
              )}
              <div>
                <span className="text-muted-foreground block mb-1">Location</span>
                <span className="font-semibold text-foreground">{data.city ? `${data.city}, ` : ''}{data.state || data.country}</span>
              </div>
            </div>
          </Card>

          {/* What's Next */}
          <Card className="p-6 bg-primary/5 border border-primary/10 text-left">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Sparkles className="h-5 w-5 text-primary" />
              </div>
              <h3 className="text-lg font-bold text-foreground">What Happens Next?</h3>
            </div>
            <ul className="space-y-3 text-sm">
              <li className="flex items-start gap-3">
                <div className="h-5 w-5 rounded-full bg-success/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                </div>
                <span className="text-foreground/80">We've matched you with personalized opportunities across scholarships, hackathons, bounties, and competitions</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="h-5 w-5 rounded-full bg-success/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                </div>
                <span className="text-foreground/80">Your dashboard is ready with prioritized deadlines and match scores</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="h-5 w-5 rounded-full bg-success/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                </div>
                <span className="text-foreground/80">Our AI assistant is available 24/7 to help you find more opportunities and answer questions</span>
              </li>
            </ul>
          </Card>

          <Button
            size="lg"
            className="w-full h-12 text-lg font-bold shadow-xl shadow-primary/25 hover:shadow-primary/40 transition-all hover:scale-[1.02]"
            onClick={onComplete}
            disabled={loading}
          >
            Show Me My Opportunities
          </Button>
        </div>
      )}
    </div>
  );
};

export default Step9Complete;
