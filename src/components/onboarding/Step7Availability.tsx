import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { OnboardingData } from '@/pages/Onboarding';
import { Clock, Calendar, Zap, Flame } from 'lucide-react';

interface Step7Props {
  data: OnboardingData;
  onNext: (data: Partial<OnboardingData>) => void;
}

const timeCommitmentOptions = [
  {
    id: 'few_hours',
    icon: Zap,
    title: 'A few hours',
    subtitle: 'Bounties & quick competitions',
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/10 hover:bg-yellow-500/20 border-yellow-500/20',
  },
  {
    id: 'weekends',
    icon: Calendar,
    title: 'Weekends',
    subtitle: '48-hour hackathons',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10 hover:bg-blue-500/20 border-blue-500/20',
  },
  {
    id: 'ongoing',
    icon: Clock,
    title: 'Ongoing commitment',
    subtitle: 'Part-time projects',
    color: 'text-purple-400',
    bgColor: 'bg-primary/10 hover:bg-primary/20 border-primary/20',
  },
  {
    id: 'flexible',
    icon: Flame,
    title: 'Flexible',
    subtitle: 'Depends on the opportunity',
    color: 'text-green-400',
    bgColor: 'bg-green-500/10 hover:bg-green-500/20 border-green-500/20',
  },
];

const availabilityOptions = [
  {
    id: 'immediate',
    title: 'Immediately',
    subtitle: 'I can start today',
    priority: 'urgent',
  },
  {
    id: 'this_week',
    title: 'This week',
    subtitle: 'Within the next 7 days',
    priority: 'high',
  },
  {
    id: 'this_month',
    title: 'This month',
    subtitle: 'Within 30 days',
    priority: 'medium',
  },
  {
    id: 'planning',
    title: 'Planning ahead',
    subtitle: '2-3 months out',
    priority: 'low',
  },
];

const Step7Availability = ({ data, onNext }: Step7Props) => {
  const [timeCommitment, setTimeCommitment] = useState<string>(data.timeCommitment || '');
  const [availability, setAvailability] = useState<string>(data.availability || '');
  const [urgentDeadline, setUrgentDeadline] = useState<string>(data.urgentDeadline || '');

  const handleContinue = () => {
    onNext({ 
      timeCommitment, 
      availability,
      ...(availability === 'immediate' && urgentDeadline ? { urgentDeadline } : {})
    });
  };

  const showUrgentDeadline = data.motivation?.includes('urgent') || availability === 'immediate';

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold text-foreground">
          How much time can you dedicate?
        </h2>
        <p className="text-muted-foreground">
          This helps us match you with the right opportunities
        </p>
      </div>

      <div className="space-y-4">
        <Label className="text-base">Time Commitment</Label>
        <div className="grid gap-3">
          {timeCommitmentOptions.map((option) => {
            const Icon = option.icon;
            const isSelected = timeCommitment === option.id;

            return (
              <Card
                key={option.id}
                className={`p-4 cursor-pointer transition-all border-2 ${
                  isSelected
                    ? `${option.bgColor} border-opacity-100`
                    : 'bg-card/50 hover:bg-card border-border/50'
                }`}
                onClick={() => setTimeCommitment(option.id)}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`p-2 rounded-lg ${
                      isSelected ? option.bgColor : 'bg-muted'
                    }`}
                  >
                    <Icon className={`h-5 w-5 ${isSelected ? option.color : 'text-muted-foreground'}`} />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-foreground">
                      {option.title}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {option.subtitle}
                    </p>
                  </div>
                  <div
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                      isSelected
                        ? 'bg-primary border-primary'
                        : 'border-muted-foreground/30'
                    }`}
                  >
                    {isSelected && (
                      <div className="w-2.5 h-2.5 bg-background rounded-full" />
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      <div className="space-y-4">
        <Label className="text-base">When are you available?</Label>
        <div className="grid gap-3">
          {availabilityOptions.map((option) => {
            const isSelected = availability === option.id;

            return (
              <Card
                key={option.id}
                className={`p-4 cursor-pointer transition-all border-2 ${
                  isSelected
                    ? 'bg-primary/10 hover:bg-primary/20 border-primary/20 border-opacity-100'
                    : 'bg-card/50 hover:bg-card border-border/50'
                }`}
                onClick={() => setAvailability(option.id)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-foreground">
                      {option.title}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {option.subtitle}
                    </p>
                  </div>
                  <div
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                      isSelected
                        ? 'bg-primary border-primary'
                        : 'border-muted-foreground/30'
                    }`}
                  >
                    {isSelected && (
                      <div className="w-2.5 h-2.5 bg-background rounded-full" />
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {showUrgentDeadline && (
        <div className="space-y-2 animate-fade-in">
          <Label htmlFor="deadline">Do you have a specific deadline? (Optional)</Label>
          <Input
            id="deadline"
            type="date"
            value={urgentDeadline}
            onChange={(e) => setUrgentDeadline(e.target.value)}
            min={new Date().toISOString().split('T')[0]}
            className="bg-background"
          />
          <p className="text-xs text-muted-foreground">
            We'll prioritize opportunities with fast turnaround
          </p>
        </div>
      )}

      {availability && (
        <div className="p-4 rounded-lg bg-primary/10 border border-primary/20 animate-fade-in">
          <p className="text-sm text-foreground">
            {availability === 'immediate' && '⚡ We\'ll show you opportunities that can start today!'}
            {availability === 'this_week' && '🎯 We\'ll prioritize this week\'s deadlines.'}
            {availability === 'this_month' && '📅 We\'ll show opportunities closing this month.'}
            {availability === 'planning' && '🔮 We\'ll include long-term opportunities with future deadlines.'}
          </p>
        </div>
      )}

      <Button
        onClick={handleContinue}
        disabled={!timeCommitment || !availability}
        className="w-full"
        size="lg"
      >
        Continue
      </Button>
    </div>
  );
};

export default Step7Availability;
