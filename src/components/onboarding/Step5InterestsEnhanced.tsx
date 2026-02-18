import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { OnboardingData } from '@/pages/Onboarding';
import { X, Sparkles } from 'lucide-react';

interface Step5Props {
  data: OnboardingData;
  onNext: (data: Partial<OnboardingData>) => void;
}

const interestCategories = {
  'Academic Fields': [
    'STEM',
    'Computer Science',
    'Engineering',
    'Data Science',
    'Business',
    'Arts & Design',
    'Healthcare',
    'Social Sciences',
    'Education',
    'Law'
  ],
  'Technical Skills': [
    'Web Development',
    'Mobile Apps',
    'AI/Machine Learning',
    'Blockchain',
    'Cybersecurity',
    'Game Development',
    'Cloud Computing'
  ],
  'Activities & Causes': [
    'Community Service',
    'Leadership',
    'Entrepreneurship',
    'Environment',
    'Social Justice',
    'Writing',
    'Athletics',
    'Music',
    'Debate'
  ]
};

const Step5InterestsEnhanced: React.FC<Step5Props> = ({ data, onNext }) => {
  const [financialNeed, setFinancialNeed] = useState(data.financialNeed || 20000);
  const [notSure, setNotSure] = useState(!data.financialNeed);
  const [selectedInterests, setSelectedInterests] = useState<string[]>(data.interests || []);
  const [customInterest, setCustomInterest] = useState('');

  const toggleInterest = (interest: string) => {
    setSelectedInterests(
      selectedInterests.includes(interest)
        ? selectedInterests.filter(i => i !== interest)
        : [...selectedInterests, interest]
    );
  };

  const addCustomInterest = () => {
    const trimmed = customInterest.trim();
    if (trimmed && !selectedInterests.includes(trimmed)) {
      setSelectedInterests([...selectedInterests, trimmed]);
      setCustomInterest('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addCustomInterest();
    }
  };

  const removeInterest = (interest: string) => {
    setSelectedInterests(selectedInterests.filter(i => i !== interest));
  };

  const handleContinue = () => {
    onNext({
      financialNeed: notSure ? undefined : financialNeed,
      interests: selectedInterests,
    });
  };

  const getMatchPrediction = () => {
    const count = selectedInterests.length;
    if (count >= 5) return "Excellent! You'll match with 100+ opportunities";
    if (count >= 3) return "Great! You'll match with 70+ opportunities";
    if (count >= 1) return "Good start! You'll match with 40+ opportunities";
    return "Select interests to see predictions";
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
      <div className="text-center space-y-3">
        <h1 className="text-3xl font-bold text-foreground">
          What are you passionate about?
        </h1>
        <p className="text-lg text-muted-foreground">
          Select all that apply - the more we know, the better we can match you!
        </p>
      </div>

      <div className="max-w-3xl mx-auto space-y-8">
        {/* Financial Need */}
        <div className="space-y-4 p-6 bg-muted/30 border border-border rounded-xl">
          <Label className="text-lg font-semibold text-foreground flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Financial Need (Optional)
          </Label>
          <p className="text-sm text-muted-foreground">
            Helps us prioritize high-value opportunities for you
          </p>
          
          {!notSure && (
            <>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground font-medium">Annual Need</span>
                <span className="text-2xl font-bold text-primary">
                  ${financialNeed.toLocaleString()}
                </span>
              </div>
              <Slider
                value={[financialNeed]}
                onValueChange={(value) => setFinancialNeed(value[0])}
                min={0}
                max={50000}
                step={5000}
                className="w-full"
              />
            </>
          )}
          
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="notSure"
              checked={notSure}
              onChange={(e) => setNotSure(e.target.checked)}
              className="h-4 w-4"
            />
            <Label htmlFor="notSure" className="cursor-pointer text-sm">
              I'm not sure / Prefer not to say
            </Label>
          </div>
        </div>

        {/* Interests by Category */}
        <div className="space-y-6">
          <h3 className="text-xl font-semibold">Your Skills & Interests</h3>
          
          {Object.entries(interestCategories).map(([category, options]) => (
            <div key={category} className="space-y-3">
              <h4 className="text-base font-semibold text-foreground/90">{category}</h4>
              <div className="flex flex-wrap gap-2">
                {options.map((interest) => (
                  <button
                    key={interest}
                    type="button"
                    onClick={() => toggleInterest(interest)}
                    className={`
                      px-4 py-2 rounded-full text-sm font-medium transition-all
                      ${
                        selectedInterests.includes(interest)
                          ? 'bg-primary text-primary-foreground shadow-md scale-105'
                          : 'bg-muted hover:bg-muted/80 hover:scale-105 border border-border'
                      }
                    `}
                  >
                    {interest}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Custom Interests */}
        <div className="space-y-3">
          <Label htmlFor="custom" className="text-base font-semibold">
            Add Your Own (Optional)
          </Label>
          <div className="flex gap-2">
            <Input
              id="custom"
              placeholder="e.g., Robotics, Photography, etc."
              value={customInterest}
              onChange={(e) => setCustomInterest(e.target.value)}
              onKeyDown={handleKeyPress}
              className="flex-1"
            />
            <Button 
              type="button" 
              onClick={addCustomInterest}
              variant="outline"
            >
              Add
            </Button>
          </div>
        </div>

        {/* Selected Interests */}
        {selectedInterests.length > 0 && (
          <div className="space-y-3">
            <Label className="text-base font-semibold">
              Selected ({selectedInterests.length})
            </Label>
            <div className="flex flex-wrap gap-2">
              {selectedInterests.map((interest) => (
                <Badge
                  key={interest}
                  variant="secondary"
                  className="px-3 py-1.5 text-sm"
                >
                  {interest}
                  <button
                    onClick={() => removeInterest(interest)}
                    className="ml-2 hover:text-destructive"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Real-time Match Prediction */}
        <div className="text-center p-4 bg-primary/10 border border-primary/20 rounded-lg">
          <p className="text-sm font-medium text-primary">
            {getMatchPrediction()}
          </p>
        </div>
      </div>

      <div className="flex justify-end pt-4">
        <Button
          onClick={handleContinue}
          disabled={selectedInterests.length === 0}
          size="lg"
          className="min-w-32"
        >
          Continue
        </Button>
      </div>
    </div>
  );
};

export default Step5InterestsEnhanced;
