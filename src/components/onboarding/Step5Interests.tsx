import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { OnboardingData } from '@/pages/Onboarding';
import { X, Plus, Sparkles } from 'lucide-react';

interface Step5Props {
  data: OnboardingData;
  onNext: (data: Partial<OnboardingData>) => void;
}

const interestCategories = {
  'Academic Fields': [
    'STEM',
    'Computer Science',
    'Engineering',
    'Business',
    'Biology',
    'Arts',
    'Healthcare',
    'Social Sciences',
    'Education',
    'Law',
  ],
  'Technical Skills': [
    'Web Development',
    'Mobile Apps',
    'AI/ML',
    'Blockchain',
    'Cybersecurity',
    'Data Science',
    'Game Development',
    'Cloud Computing',
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
    'Debate',
    'Volunteering',
  ],
};

const Step5Interests: React.FC<Step5Props> = ({ data, onNext }) => {
  const [selectedInterests, setSelectedInterests] = useState<string[]>(data.interests || []);
  const [customInterest, setCustomInterest] = useState('');
  const [expandedCategory, setExpandedCategory] = useState<string | null>('Academic Fields');

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
    if (selectedInterests.length >= 2) {
      onNext({ interests: selectedInterests });
    }
  };

  // Calculate estimated matches
  const estimatedMatches = Math.min(120, selectedInterests.length * 12 + 40);

  // Check if it's a tech-related profile
  const hasTechSkills = selectedInterests.some(i => 
    interestCategories['Technical Skills'].includes(i) || 
    ['Computer Science', 'Engineering', 'STEM'].includes(i)
  );

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="text-center space-y-3">
        <h1 className="text-3xl md:text-4xl font-bold text-foreground tracking-tight">
          What are you passionate about <br />
          <span className="text-primary">or skilled in?</span>
        </h1>
        <p className="text-lg text-muted-foreground max-w-lg mx-auto">
          Select at least 2 interests to help us find the best matches
        </p>
      </div>

      {/* Selected Interests */}
      {selectedInterests.length > 0 && (
        <div className="max-w-3xl mx-auto">
          <Card className="p-4 bg-primary/5 border-primary/20">
            <div className="flex flex-wrap gap-2">
              {selectedInterests.map((interest) => (
                <Badge
                  key={interest}
                  variant="secondary"
                  className="pl-3 pr-2 py-1.5 text-sm bg-primary/20 hover:bg-primary/30 border-primary/30"
                >
                  {interest}
                  <button
                    onClick={() => removeInterest(interest)}
                    className="ml-2 hover:text-destructive transition-colors"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Interest Categories */}
      <div className="max-w-3xl mx-auto space-y-4">
        {Object.entries(interestCategories).map(([category, interests]) => {
          // Only show Technical Skills if they've selected CS/STEM related fields
          if (category === 'Technical Skills' && !hasTechSkills) {
            return null;
          }

          return (
            <Card key={category} className="p-4 border-border/50">
              <button
                onClick={() => setExpandedCategory(expandedCategory === category ? null : category)}
                className="w-full flex items-center justify-between mb-3"
              >
                <h3 className="font-semibold text-base text-foreground">{category}</h3>
                <span className="text-xs text-muted-foreground">
                  {selectedInterests.filter(i => interests.includes(i)).length} selected
                </span>
              </button>
              
              {(expandedCategory === category || selectedInterests.some(i => interests.includes(i))) && (
                <div className="flex flex-wrap gap-2">
                  {interests.map((interest) => {
                    const isSelected = selectedInterests.includes(interest);
                    return (
                      <Badge
                        key={interest}
                        variant={isSelected ? 'default' : 'outline'}
                        className={`cursor-pointer transition-all hover:scale-105 ${
                          isSelected
                            ? 'bg-primary text-primary-foreground border-primary'
                            : 'hover:border-primary/50'
                        }`}
                        onClick={() => toggleInterest(interest)}
                      >
                        {interest}
                      </Badge>
                    );
                  })}
                </div>
              )}
            </Card>
          );
        })}

        {/* Custom Interest Input */}
        <Card className="p-4 border-border/50">
          <Label className="text-sm font-medium mb-2 block">Add your own interest</Label>
          <div className="flex gap-2">
            <Input
              placeholder="e.g., Photography, Robotics, Poetry..."
              value={customInterest}
              onChange={(e) => setCustomInterest(e.target.value)}
              onKeyPress={handleKeyPress}
              className="flex-1 bg-background"
            />
            <Button
              type="button"
              variant="secondary"
              size="icon"
              onClick={addCustomInterest}
              disabled={!customInterest.trim()}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      </div>

      {/* Real-time Feedback */}
      {selectedInterests.length > 0 && (
        <div className="max-w-3xl mx-auto p-4 bg-green-500/10 border border-green-500/20 rounded-xl flex gap-3 items-start animate-fade-in">
          <Sparkles className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-foreground font-semibold">
              Looking good! Students with these interests typically match with {estimatedMatches}+ opportunities.
            </p>
            {selectedInterests.length >= 5 && (
              <p className="text-xs text-muted-foreground mt-1">
                💡 Tip: More interests = more opportunities, but focus on what you're truly passionate about.
              </p>
            )}
          </div>
        </div>
      )}

      <div className="max-w-md mx-auto">
        <Button
          onClick={handleContinue}
          disabled={selectedInterests.length < 2}
          className="w-full h-11 shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all"
          size="lg"
        >
          Continue {selectedInterests.length < 2 && `(select ${2 - selectedInterests.length} more)`}
        </Button>
        {selectedInterests.length < 2 && (
          <p className="text-xs text-center text-muted-foreground mt-2">
            Please select at least 2 interests to continue
          </p>
        )}
      </div>
    </div>
  );
};

export default Step5Interests;
