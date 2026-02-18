import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Check, Clock, Calendar } from 'lucide-react';

interface Step6AvailabilityProps {
  data: {
    timeCommitment?: string;
    availability?: string;
  };
  onNext: (data: { timeCommitment: string; availability: string }) => void;
  onBack: () => void;
}

const timeOptions = [
  {
    id: 'quick',
    icon: Clock,
    title: 'A few hours',
    subtitle: 'Quick wins',
    description: 'Perfect for bounties and quick competitions'
  },
  {
    id: 'weekend',
    icon: Calendar,
    title: 'Weekends',
    subtitle: '48-hour hackathons',
    description: 'Join hackathons and weekend challenges'
  },
  {
    id: 'ongoing',
    icon: Calendar,
    title: 'Ongoing commitment',
    subtitle: 'Part-time projects',
    description: 'Longer projects and research opportunities'
  },
  {
    id: 'flexible',
    icon: Check,
    title: 'Flexible',
    subtitle: 'Depends on opportunity',
    description: 'I can adjust based on the prize/value'
  }
];

const availabilityOptions = [
  {
    id: 'immediate',
    emoji: '⚡',
    title: 'Immediately',
    subtitle: 'I can start today',
    priority: 'urgent'
  },
  {
    id: 'this_week',
    emoji: '📅',
    title: 'This week',
    subtitle: 'Within 7 days',
    priority: 'high'
  },
  {
    id: 'this_month',
    emoji: '🗓️',
    title: 'This month',
    subtitle: 'Within 30 days',
    priority: 'medium'
  },
  {
    id: 'planning',
    emoji: '🎯',
    title: 'Planning ahead',
    subtitle: '2-3 months out',
    priority: 'low'
  }
];

const Step6Availability = ({ data, onNext, onBack }: Step6AvailabilityProps) => {
  const [timeCommitment, setTimeCommitment] = useState(data.timeCommitment || '');
  const [availability, setAvailability] = useState(data.availability || '');

  const handleNext = () => {
    if (!timeCommitment || !availability) return;
    onNext({ timeCommitment, availability });
  };

  const getPriorityMessage = () => {
    const selected = availabilityOptions.find(o => o.id === availability);
    if (!selected) return null;

    const messages = {
      urgent: "🚀 We'll show you opportunities closing this week with fast turnarounds!",
      high: "⚡ Perfect timing! We'll prioritize opportunities starting soon.",
      medium: "📊 Great! We'll show you a mix of immediate and upcoming opportunities.",
      low: "🎓 Smart planning! We'll focus on traditional scholarships with longer deadlines."
    };

    return messages[selected.priority as keyof typeof messages];
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold">How much time can you dedicate?</h2>
        <p className="text-muted-foreground text-lg">
          This helps us match you with the right opportunities
        </p>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Time Commitment</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          {timeOptions.map((option) => {
            const Icon = option.icon;
            return (
              <Card
                key={option.id}
                className={`
                  relative p-4 cursor-pointer transition-all hover:shadow-md
                  ${timeCommitment === option.id
                    ? 'border-primary bg-primary/5 shadow-sm'
                    : 'border-border hover:border-primary/50'
                  }
                `}
                onClick={() => setTimeCommitment(option.id)}
              >
                {timeCommitment === option.id && (
                  <div className="absolute top-3 right-3 bg-primary text-primary-foreground rounded-full p-1">
                    <Check className="h-3 w-3" />
                  </div>
                )}
                <div className="flex gap-3">
                  <div className={`
                    h-10 w-10 rounded-lg flex items-center justify-center shrink-0
                    ${timeCommitment === option.id ? 'bg-primary/20' : 'bg-muted'}
                  `}>
                    <Icon className={`h-5 w-5 ${timeCommitment === option.id ? 'text-primary' : 'text-muted-foreground'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold">{option.title}</h4>
                    <p className="text-sm text-muted-foreground">{option.subtitle}</p>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">When are you available?</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          {availabilityOptions.map((option) => (
            <Card
              key={option.id}
              className={`
                relative p-4 cursor-pointer transition-all hover:shadow-md
                ${availability === option.id
                  ? 'border-primary bg-primary/5 shadow-sm'
                  : 'border-border hover:border-primary/50'
                }
              `}
              onClick={() => setAvailability(option.id)}
            >
              {availability === option.id && (
                <div className="absolute top-3 right-3 bg-primary text-primary-foreground rounded-full p-1">
                  <Check className="h-3 w-3" />
                </div>
              )}
              <div className="flex gap-3 items-center">
                <div className="text-3xl">{option.emoji}</div>
                <div className="flex-1">
                  <h4 className="font-semibold">{option.title}</h4>
                  <p className="text-sm text-muted-foreground">{option.subtitle}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {getPriorityMessage() && (
        <div className="text-center p-4 bg-primary/10 border border-primary/20 rounded-lg animate-in fade-in slide-in-from-bottom-2">
          <p className="text-sm font-medium">{getPriorityMessage()}</p>
        </div>
      )}

      <div className="flex justify-between pt-4">
        <Button variant="outline" onClick={onBack} size="lg">
          Back
        </Button>
        <Button
          onClick={handleNext}
          disabled={!timeCommitment || !availability}
          size="lg"
          className="min-w-32"
        >
          Continue
        </Button>
      </div>
    </div>
  );
};

export default Step6Availability;
