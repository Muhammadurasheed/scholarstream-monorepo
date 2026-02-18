import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Check, Download, Home, TrendingUp } from 'lucide-react';
import Confetti from 'react-confetti';
import { useEffect, useState } from 'react';
import type { Scholarship } from '@/types/scholarship';

interface Step6SuccessProps {
  scholarship: Scholarship;
  confirmationNumber: string;
  applicationId: string;
}

export default function Step6Success({ scholarship, confirmationNumber, applicationId }: Step6SuccessProps) {
  const navigate = useNavigate();
  const [windowSize, setWindowSize] = useState({ width: window.innerWidth, height: window.innerHeight });

  useEffect(() => {
    const handleResize = () => {
      setWindowSize({ width: window.innerWidth, height: window.innerHeight });
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-background to-blue-50 dark:from-green-950/20 dark:via-background dark:to-blue-950/20 flex items-center justify-center p-4">
      <Confetti
        width={windowSize.width}
        height={windowSize.height}
        recycle={false}
        numberOfPieces={500}
        gravity={0.3}
      />

      <div className="max-w-2xl w-full space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
        {/* Success Icon */}
        <div className="flex justify-center">
          <div className="relative">
            <div className="h-24 w-24 rounded-full bg-green-500 flex items-center justify-center animate-in zoom-in duration-500">
              <Check className="h-12 w-12 text-white" />
            </div>
            <div className="absolute inset-0 h-24 w-24 rounded-full bg-green-500 animate-ping opacity-20" />
          </div>
        </div>

        {/* Success Message */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-foreground">Application Submitted! 🎉</h1>
          <p className="text-xl text-muted-foreground">
            You've applied for {scholarship.name}
          </p>
        </div>

        {/* Confirmation Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-center">Confirmation Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
              <span className="text-sm text-muted-foreground">Confirmation Number</span>
              <span className="text-lg font-mono font-bold text-foreground">{confirmationNumber}</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="p-3 bg-muted rounded-lg">
                <p className="text-muted-foreground mb-1">Scholarship</p>
                <p className="font-semibold text-foreground">{scholarship.name}</p>
              </div>

              <div className="p-3 bg-muted rounded-lg">
                <p className="text-muted-foreground mb-1">Amount</p>
                <p className="font-semibold text-green-600 text-lg">{scholarship.amount_display}</p>
              </div>

              <div className="p-3 bg-muted rounded-lg">
                <p className="text-muted-foreground mb-1">Submitted On</p>
                <p className="font-semibold text-foreground">{new Date().toLocaleDateString()}</p>
              </div>

              <div className="p-3 bg-muted rounded-lg">
                <p className="text-muted-foreground mb-1">Decision Expected</p>
                <p className="font-semibold text-foreground">Check your email</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Next Steps */}
        <Card>
          <CardHeader>
            <CardTitle>What Happens Next?</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-3">
              <div className="h-8 w-8 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-sm font-bold text-blue-600">1</span>
              </div>
              <div>
                <p className="font-medium text-foreground">Your application is being reviewed</p>
                <p className="text-sm text-muted-foreground">The scholarship committee will evaluate all applications</p>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="h-8 w-8 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-sm font-bold text-purple-600">2</span>
              </div>
              <div>
                <p className="font-medium text-foreground">Finalists will be notified</p>
                <p className="text-sm text-muted-foreground">Check your email regularly for updates</p>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="h-8 w-8 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-sm font-bold text-green-600">3</span>
              </div>
              <div>
                <p className="font-medium text-foreground">Winners announced</p>
                <p className="text-sm text-muted-foreground">All applicants will be notified of the final decision</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            onClick={() => navigate('/dashboard')}
            size="lg"
            className="flex-1 gap-2"
          >
            <Home className="h-5 w-5" />
            Return to Dashboard
          </Button>

          <Button
            onClick={() => navigate('/dashboard')}
            size="lg"
            variant="outline"
            className="flex-1 gap-2"
          >
            <TrendingUp className="h-5 w-5" />
            Apply to Similar Scholarships
          </Button>
        </div>

        <div className="text-center text-sm text-muted-foreground">
          A confirmation email has been sent to your email address
        </div>
      </div>
    </div>
  );
}
