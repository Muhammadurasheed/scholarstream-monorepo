import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Card } from '@/components/ui/card';
import { OnboardingData } from '@/pages/Onboarding';
import { Lock } from 'lucide-react';

interface Step4Props {
  data: OnboardingData;
  onNext: (data: Partial<OnboardingData>) => void;
  onSkip: (data: Partial<OnboardingData>) => void;
}

const backgroundOptions = [
  { id: 'first-gen', label: 'First-generation college student', tooltip: 'Parents didn\'t complete 4-year degree' },
  { id: 'international', label: 'International student', tooltip: 'Studying from outside the country' },
  { id: 'daca', label: 'DACA recipient or undocumented', tooltip: 'DACA or undocumented student status' },
  { id: 'lgbtq', label: 'LGBTQ+ identifying', tooltip: 'Part of LGBTQ+ community' },
  { id: 'disability', label: 'Student with disability', tooltip: 'Physical or learning disability' },
  { id: 'minority', label: 'Racial or ethnic minority', tooltip: 'Underrepresented racial/ethnic group' },
  { id: 'low-income', label: 'Low-income / Pell Grant eligible', tooltip: 'Financial need-based eligibility' },
  { id: 'veteran', label: 'Veteran or military family', tooltip: 'Military service or dependent' },
  { id: 'foster', label: 'Foster care experience', tooltip: 'Current or former foster youth' },
  { id: 'prefer-not', label: 'Prefer not to say', tooltip: 'Skip all background questions' },
];

const Step4Background: React.FC<Step4Props> = ({ data, onNext, onSkip }) => {
  const [selected, setSelected] = useState<string[]>(data.background || []);

  const handleToggle = (optionId: string) => {
    if (optionId === 'prefer-not') {
      setSelected(selected.includes('prefer-not') ? [] : ['prefer-not']);
    } else {
      if (selected.includes('prefer-not')) {
        setSelected([optionId]);
      } else {
        setSelected(
          selected.includes(optionId)
            ? selected.filter(id => id !== optionId)
            : [...selected, optionId]
        );
      }
    }
  };

  const handleContinue = () => {
    onNext({ background: selected });
  };

  const handleSkipStep = () => {
    onSkip({ background: [] });
  };

  return (
    <div className="space-y-8 animate-slide-up">
      <div className="text-center space-y-3">
        <p className="text-sm text-primary font-semibold tracking-wide uppercase">Step 4 of 6</p>
        <h1 className="text-3xl md:text-4xl font-bold text-foreground tracking-tight">
          Help us find opportunities <br />
          <span className="text-primary">designed for you</span>
        </h1>
        <p className="text-lg text-muted-foreground max-w-lg mx-auto">
          All questions are completely optional and kept private.
        </p>
      </div>

      <Card className="max-w-2xl mx-auto p-4 bg-primary/5 border border-primary/10 shadow-sm flex gap-3 items-start">
        <div className="p-2 bg-background rounded-full shadow-sm">
          <Lock className="h-4 w-4 text-primary" />
        </div>
        <div>
          <p className="font-semibold text-foreground text-sm">Your privacy matters</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            We only use this data to match you with specific scholarships for underrepresented groups.
          </p>
        </div>
      </Card>

      <div className="max-w-2xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-3">
        {backgroundOptions.map((option) => {
          const isSelected = selected.includes(option.id);
          const isPreferNot = option.id === 'prefer-not';
          const isDisabled = !isPreferNot && selected.includes('prefer-not');

          return (
            <div
              key={option.id}
              className={`
                relative p-4 rounded-xl border transition-all duration-200 cursor-pointer
                ${isDisabled ? 'opacity-50 cursor-not-allowed bg-secondary/50' : 'hover:border-primary/50 hover:shadow-sm'}
                ${isSelected
                  ? 'border-primary bg-primary/5 shadow-md shadow-primary/5'
                  : 'border-border bg-card'
                }
              `}
              onClick={() => !isDisabled && handleToggle(option.id)}
            >
              <div className="flex items-start gap-3">
                <Checkbox
                  checked={isSelected}
                  disabled={isDisabled}
                  className={`mt-0.5 ${isSelected ? 'border-primary data-[state=checked]:bg-primary' : ''}`}
                />
                <div className="flex-1">
                  <p className={`font-medium text-sm ${isSelected ? 'text-primary' : 'text-foreground'}`}>
                    {option.label}
                  </p>
                  {option.tooltip && (
                    <p className="text-xs text-muted-foreground mt-0.5">{option.tooltip}</p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="max-w-md mx-auto flex gap-3">
        <Button variant="ghost" onClick={handleSkipStep} className="flex-1 h-11 text-muted-foreground hover:text-foreground">
          Skip
        </Button>
        <Button
          onClick={handleContinue}
          className="flex-[2] h-11 shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all"
        >
          Continue
        </Button>
      </div>
    </div>
  );
};

export default Step4Background;