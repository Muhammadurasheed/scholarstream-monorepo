import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { OnboardingData } from '@/pages/Onboarding';
import { DollarSign, Lightbulb, Calendar } from 'lucide-react';
import { Input } from '@/components/ui/input';

interface Step4Props {
  data: OnboardingData;
  onNext: (data: Partial<OnboardingData>) => void;
  onSkip: (data: Partial<OnboardingData>) => void;
}

const majors = [
  'Computer Science', 'Engineering', 'Business', 'Biology', 'Psychology',
  'English', 'Mathematics', 'Political Science', 'Economics', 'Chemistry',
  'History', 'Art', 'Music', 'Education', 'Nursing', 'Other'
];

const Step4Profile: React.FC<Step4Props> = ({ data, onNext, onSkip }) => {
  const [gpa, setGpa] = useState(data.gpa || 3.5);
  const [major, setMajor] = useState(data.major || '');
  const [graduationYear, setGraduationYear] = useState(data.graduationYear || '');
  const [financialNeed, setFinancialNeed] = useState(data.financialNeed || 10000);
  const [urgentDeadline, setUrgentDeadline] = useState(data.urgentDeadline || '');

  const getLetterGrade = (gpaValue: number) => {
    if (gpaValue >= 3.7) return 'A';
    if (gpaValue >= 3.3) return 'A-';
    if (gpaValue >= 3.0) return 'B+';
    if (gpaValue >= 2.7) return 'B';
    if (gpaValue >= 2.3) return 'B-';
    if (gpaValue >= 2.0) return 'C+';
    return 'C';
  };

  const handleContinue = () => {
    onNext({ gpa, major, graduationYear, financialNeed, urgentDeadline });
  };

  const handleSkip = () => {
    onSkip({ major: major || 'Undecided', graduationYear: graduationYear || '2028' });
  };

  const showUrgentDeadline = data.motivation?.includes('urgent');

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="text-center space-y-3">
        <h1 className="text-3xl md:text-4xl font-bold text-foreground tracking-tight">
          Tell us about your <br />
          <span className="text-primary">academic profile</span>
        </h1>
        <p className="text-lg text-muted-foreground max-w-lg mx-auto">
          This helps us match you with merit-based and need-based opportunities
        </p>
      </div>

      <div className="max-w-md mx-auto space-y-6 bg-card p-8 rounded-2xl shadow-sm border border-border/50">
        {/* GPA Slider */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <Label className="text-base font-medium">GPA (4.0 scale)</Label>
            <div className="flex items-center gap-2 bg-primary/10 px-3 py-1 rounded-full">
              <span className="text-lg font-bold text-primary">
                {gpa.toFixed(1)}
              </span>
              <span className="text-sm font-medium text-primary/80">
                ({getLetterGrade(gpa)})
              </span>
            </div>
          </div>
          <Slider
            value={[gpa]}
            onValueChange={(value) => setGpa(value[0])}
            min={0}
            max={4}
            step={0.1}
            className="w-full py-4"
          />
          <p className="text-xs text-muted-foreground text-center">
            Don't worry if you're not sure - you can update this later
          </p>
        </div>

        {/* Major */}
        <div className="space-y-2">
          <Label className="text-base font-medium">Major / Intended Major</Label>
          <Select value={major} onValueChange={setMajor}>
            <SelectTrigger className="h-11 bg-background">
              <SelectValue placeholder="Select your major" />
            </SelectTrigger>
            <SelectContent className="bg-background border-border">
              {majors.map((m) => (
                <SelectItem key={m} value={m}>
                  {m}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Graduation Year */}
        <div className="space-y-2">
          <Label className="text-base font-medium">Expected Graduation Year</Label>
          <Select value={graduationYear} onValueChange={setGraduationYear}>
            <SelectTrigger className="h-11 bg-background">
              <SelectValue placeholder="Select year" />
            </SelectTrigger>
            <SelectContent className="bg-background border-border">
              {[2025, 2026, 2027, 2028, 2029, 2030, 2031].map((year) => (
                <SelectItem key={year} value={year.toString()}>
                  {year}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Financial Need */}
        <div className="space-y-4 pt-4 border-t border-border">
          <div className="flex justify-between items-center">
            <Label className="text-base font-medium flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-primary" />
              Financial Need
            </Label>
            <div className="flex items-center gap-1 bg-green-500/10 px-3 py-1 rounded-full">
              <span className="text-lg font-bold text-green-600">
                ${financialNeed.toLocaleString()}
              </span>
            </div>
          </div>
          <Slider
            value={[financialNeed]}
            onValueChange={(value) => setFinancialNeed(value[0])}
            min={0}
            max={50000}
            step={1000}
            className="w-full py-4"
          />
          <p className="text-xs text-muted-foreground text-center">
            How much funding do you need per year?
          </p>
        </div>

        {showUrgentDeadline && (
          <div className="space-y-2 pt-4 border-t border-border animate-fade-in">
            <Label htmlFor="urgent-deadline" className="text-base font-medium flex items-center gap-2">
              <Calendar className="h-4 w-4 text-red-400" />
              Do you have an urgent deadline?
            </Label>
            <Input
              id="urgent-deadline"
              type="date"
              value={urgentDeadline}
              onChange={(e) => setUrgentDeadline(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className="bg-background h-11"
            />
            <p className="text-xs text-muted-foreground">
              We'll prioritize opportunities with fast turnaround
            </p>
          </div>
        )}

        {gpa >= 3.5 && (
          <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl flex gap-3 items-start animate-fade-in">
            <Lightbulb className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
            <p className="text-sm text-foreground/80">
              <span className="font-semibold text-primary">Great job!</span> Students with {gpa.toFixed(1)} GPA typically qualify for exclusive merit-based scholarships.
            </p>
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <Button variant="ghost" onClick={handleSkip} className="flex-1 h-11 text-muted-foreground hover:text-foreground">
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
    </div>
  );
};

export default Step4Profile;
