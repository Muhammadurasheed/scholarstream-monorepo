import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { OnboardingData } from '@/pages/Onboarding';
import { CheckCircle2, Sparkles, Loader2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { apiService } from '@/services/api';

interface Step6Props {
  data: OnboardingData;
  onComplete: () => void;
}

const Step6Complete: React.FC<Step6Props> = ({ data, onComplete }) => {
  const [loading, setLoading] = useState(true);
  const [loadingMessage, setLoadingMessage] = useState('Analyzing your profile...');
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    const initiateDiscovery = async () => {
      if (!user) return;

      const messages = [
        'Analyzing your profile...',
        'Searching scholarship databases...',
        'Running AI matching algorithm...',
        'Prioritizing your opportunities...',
      ];

      let messageIndex = 0;
      const interval = setInterval(() => {
        messageIndex++;
        if (messageIndex < messages.length) {
          setLoadingMessage(messages[messageIndex]);
        }
      }, 1000);

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
        };

        await apiService.discoverScholarships(user.uid, profile);

        clearInterval(interval);
        setLoading(false);
      } catch (err: any) {
        console.error('Failed to initiate scholarship discovery:', err);
        clearInterval(interval);
        setLoading(false);
        setError('Discovery service temporarily unavailable. Your scholarships will be ready shortly.');
      }
    };

    initiateDiscovery();
  }, [user, data]);

  return (
    <div className="space-y-8 animate-scale-in text-center max-w-2xl mx-auto">
      {/* Success Icon */}
      <div className="relative py-8">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className={`h-32 w-32 rounded-full ${loading ? 'bg-primary/10 animate-pulse' : 'bg-success/10 animate-ping'}`}></div>
        </div>
        {loading ? (
          <Loader2 className="h-24 w-24 text-primary mx-auto relative z-10 animate-spin" />
        ) : (
          <CheckCircle2 className="h-24 w-24 text-success mx-auto relative z-10" />
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
            Profile complete! Your scholarships are ready.
          </p>
        )}
      </div>

      {!loading && (
        <div className="space-y-6 animate-slide-up">
          <Card className="p-6 text-left border border-border/50 shadow-sm bg-card">
            <h3 className="text-lg font-bold mb-4 text-foreground border-b border-border pb-2">Profile Summary</h3>
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
            </div>
          </Card>

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
                <span className="text-foreground/80">We've matched you with personalized scholarships</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="h-5 w-5 rounded-full bg-success/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                </div>
                <span className="text-foreground/80">Your dashboard is ready with deadlines and priorities</span>
              </li>
            </ul>
          </Card>

          <Button
            size="lg"
            className="w-full h-12 text-lg font-bold shadow-xl shadow-primary/25 hover:shadow-primary/40 transition-all hover:scale-[1.02]"
            onClick={onComplete}
            disabled={loading}
          >
            See My Opportunities
          </Button>
        </div>
      )}
    </div>
  );
};

export default Step6Complete;