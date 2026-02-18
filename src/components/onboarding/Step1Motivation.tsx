import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Check } from 'lucide-react';

interface Step1MotivationProps {
  data: { motivations?: string[] };
  onNext: (data: { motivations: string[] }) => void;
}

const motivationOptions = [
  {
    id: 'urgent',
    emoji: '💰',
    title: 'I need money urgently',
    subtitle: 'Within days/weeks',
    description: 'We\'ll prioritize hackathons and bounties with quick turnarounds'
  },
  {
    id: 'scholarships',
    emoji: '🎓',
    title: 'Looking for scholarships',
    subtitle: 'Long-term funding',
    description: 'Traditional scholarships for tuition and education expenses'
  },
  {
    id: 'hackathons',
    emoji: '💻',
    title: 'Want to join hackathons',
    subtitle: 'Win prizes & build',
    description: 'Competitive coding events with cash prizes and networking'
  },
  {
    id: 'competitions',
    emoji: '🏆',
    title: 'Data science competitions',
    subtitle: 'Kaggle & challenges',
    description: 'ML competitions and data science challenges'
  },
  {
    id: 'open',
    emoji: '🚀',
    title: 'Open to any opportunity',
    subtitle: 'Show me everything',
    description: 'A balanced mix of all opportunity types'
  }
];

const Step1Motivation = ({ data, onNext }: Step1MotivationProps) => {
  const [selected, setSelected] = useState<string[]>(data.motivations || []);

  const toggleMotivation = (id: string) => {
    setSelected(prev =>
      prev.includes(id)
        ? prev.filter(m => m !== id)
        : [...prev, id]
    );
  };

  const handleNext = () => {
    if (selected.length === 0) return;
    onNext({ motivations: selected });
  };

  const getEncouragingMessage = () => {
    if (selected.includes('urgent')) {
      return "💡 Perfect! We specialize in finding immediate opportunities with fast payouts.";
    }
    if (selected.includes('scholarships')) {
      return "📚 Great! We track 1000+ scholarships from trusted sources.";
    }
    if (selected.includes('hackathons')) {
      return "🔥 Awesome! We monitor 200+ active hackathons happening right now.";
    }
    if (selected.length > 2) {
      return "🎯 Smart choice! More selections = better personalized matches.";
    }
    return null;
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold">What brings you to ScholarStream?</h2>
        <p className="text-muted-foreground text-lg">
          Select all that apply - we'll personalize your matches
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {motivationOptions.map((option, index) => (
          <Card
            key={option.id}
            className={`
              relative p-6 cursor-pointer transition-all duration-200 hover:shadow-lg
              ${selected.includes(option.id) 
                ? 'border-primary bg-primary/5 shadow-md' 
                : 'border-border hover:border-primary/50'
              }
            `}
            style={{ animationDelay: `${index * 50}ms` }}
            onClick={() => toggleMotivation(option.id)}
          >
            {selected.includes(option.id) && (
              <div className="absolute top-4 right-4 bg-primary text-primary-foreground rounded-full p-1">
                <Check className="h-4 w-4" />
              </div>
            )}
            
            <div className="space-y-3">
              <div className="text-4xl">{option.emoji}</div>
              <div>
                <h3 className="font-semibold text-lg">{option.title}</h3>
                <p className="text-sm text-primary font-medium">{option.subtitle}</p>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {option.description}
              </p>
            </div>
          </Card>
        ))}
      </div>

      {getEncouragingMessage() && (
        <div className="text-center p-4 bg-primary/10 border border-primary/20 rounded-lg animate-in fade-in slide-in-from-bottom-2">
          <p className="text-sm font-medium">{getEncouragingMessage()}</p>
        </div>
      )}

      <div className="flex justify-between pt-4">
        <div className="text-sm text-muted-foreground">
          {selected.length > 0 && `${selected.length} selected`}
        </div>
        <Button
          onClick={handleNext}
          disabled={selected.length === 0}
          size="lg"
          className="min-w-32"
        >
          Continue
        </Button>
      </div>
    </div>
  );
};

export default Step1Motivation;
