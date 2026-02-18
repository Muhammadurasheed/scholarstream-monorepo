import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { OnboardingData } from '@/pages/Onboarding';
import { DollarSign, GraduationCap, Code, Trophy, Sparkles } from 'lucide-react';

interface Step2Props {
  data: OnboardingData;
  onNext: (data: Partial<OnboardingData>) => void;
}

const motivationOptions = [
  {
    id: 'urgent',
    icon: DollarSign,
    title: 'Urgent Funding',
    subtitle: 'I need money within days/weeks',
    description: "We'll prioritize hackathons, bounties, and quick opportunities",
    color: 'text-red-400',
    bgColor: 'bg-red-500/10 hover:bg-red-500/20 border-red-500/20',
  },
  {
    id: 'scholarships',
    icon: GraduationCap,
    title: 'Scholarships',
    subtitle: 'Long-term funding for education',
    description: 'We track 1000+ scholarships for personalized matches',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10 hover:bg-blue-500/20 border-blue-500/20',
  },
  {
    id: 'hackathons',
    icon: Code,
    title: 'Hackathons',
    subtitle: 'Join coding competitions',
    description: 'We monitor 200+ active hackathons you can win',
    color: 'text-purple-400',
    bgColor: 'bg-primary/10 hover:bg-primary/20 border-primary/20',
  },
  {
    id: 'competitions',
    icon: Trophy,
    title: 'Competitions',
    subtitle: 'Challenges and contests',
    description: 'Find competitions that match your skills',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10 hover:bg-amber-500/20 border-amber-500/20',
  },
  {
    id: 'open',
    icon: Sparkles,
    title: 'Any Opportunity',
    subtitle: "I'm open to anything that fits",
    description: 'Get a balanced mix of all opportunity types',
    color: 'text-green-400',
    bgColor: 'bg-green-500/10 hover:bg-green-500/20 border-green-500/20',
  },
];

const Step2Motivation = ({ data, onNext }: Step2Props) => {
  const [selected, setSelected] = useState<string[]>(data.motivation || []);

  const toggleSelection = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleContinue = () => {
    if (selected.length === 0) return;
    onNext({ motivation: selected });
  };

  const getEncouragingMessage = () => {
    if (selected.includes('urgent')) {
      return '🚀 We specialize in finding immediate opportunities! Let\'s find some money-making chances for you.';
    }
    if (selected.includes('scholarships')) {
      return '📚 Great! We track 1000+ scholarships. Let\'s personalize your matches.';
    }
    if (selected.includes('hackathons')) {
      return '💻 Awesome! We monitor 200+ active hackathons. Let\'s find ones you can win.';
    }
    if (selected.length > 1) {
      return '🎯 Perfect! We\'ll show you opportunities across multiple categories.';
    }
    return '✨ Let\'s find opportunities that match your goals!';
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold text-foreground">
          What brings you to ScholarStream today?
        </h2>
        <p className="text-muted-foreground">
          Select all that interest you (you can pick multiple)
        </p>
      </div>

      <div className="grid gap-4">
        {motivationOptions.map((option) => {
          const Icon = option.icon;
          const isSelected = selected.includes(option.id);

          return (
            <Card
              key={option.id}
              className={`p-6 cursor-pointer transition-all border-2 ${
                isSelected
                  ? `${option.bgColor} border-opacity-100`
                  : 'bg-card/50 hover:bg-card border-border/50'
              }`}
              onClick={() => toggleSelection(option.id)}
            >
              <div className="flex items-start gap-4">
                <div
                  className={`p-3 rounded-lg ${
                    isSelected ? option.bgColor : 'bg-muted'
                  }`}
                >
                  <Icon className={`h-6 w-6 ${isSelected ? option.color : 'text-muted-foreground'}`} />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-lg text-foreground mb-1">
                    {option.title}
                  </h3>
                  <p className="text-sm text-muted-foreground mb-2">
                    {option.subtitle}
                  </p>
                  <p className="text-xs text-muted-foreground/80">
                    {option.description}
                  </p>
                </div>
                <div
                  className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                    isSelected
                      ? 'bg-primary border-primary'
                      : 'border-muted-foreground/30'
                  }`}
                >
                  {isSelected && (
                    <div className="w-3 h-3 bg-background rounded-full" />
                  )}
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {selected.length > 0 && (
        <div className="p-4 rounded-lg bg-primary/10 border border-primary/20 animate-fade-in">
          <p className="text-sm text-foreground">{getEncouragingMessage()}</p>
        </div>
      )}

      <Button
        onClick={handleContinue}
        disabled={selected.length === 0}
        className="w-full"
        size="lg"
      >
        Continue
      </Button>
    </div>
  );
};

export default Step2Motivation;
