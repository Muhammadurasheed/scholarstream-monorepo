import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { OnboardingData } from '@/pages/Onboarding';
import { GraduationCap, Book, Award, HelpCircle, TrendingUp } from 'lucide-react';

interface Step3Props {
  data: OnboardingData;
  onNext: (data: Partial<OnboardingData>) => void;
}

const academicStatuses = [
  { id: 'high-school', label: 'High School Senior', icon: GraduationCap, desc: 'Preparing for college', oppCount: '500+' },
  { id: 'undergraduate', label: 'Undergraduate', icon: Book, desc: 'Currently in college', hasYear: true, oppCount: '800+' },
  { id: 'graduate', label: 'Graduate Student', icon: Award, desc: "Master's or PhD program", oppCount: '300+' },
  { id: 'other', label: 'Other', icon: HelpCircle, desc: 'Gap year, community college, etc.', oppCount: '200+' },
];

const Step3Academic: React.FC<Step3Props> = ({ data, onNext }) => {
  const [academicStatus, setAcademicStatus] = useState(data.academicStatus);
  const [year, setYear] = useState(data.year || '');
  const [school, setSchool] = useState(data.school);
  const [showSchool, setShowSchool] = useState(false);

  const selectedStatus = academicStatuses.find(s => s.id === academicStatus);

  const handleStatusSelect = (statusId: string) => {
    setAcademicStatus(statusId);
    setShowSchool(true);
  };

  const handleContinue = () => {
    if (academicStatus) {
      onNext({
        academicStatus,
        year: selectedStatus?.hasYear ? year : undefined,
        school: school || ''
      });
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="text-center space-y-3">
        <h1 className="text-3xl md:text-4xl font-bold text-foreground tracking-tight">
          Where are you in your <br />
          <span className="text-primary">academic journey?</span>
        </h1>
        <p className="text-lg text-muted-foreground max-w-lg mx-auto">
          This helps us find opportunities relevant to your level
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl mx-auto">
        {academicStatuses.map((status) => {
          const Icon = status.icon;
          const isSelected = academicStatus === status.id;

          return (
            <Card
              key={status.id}
              className={`p-6 cursor-pointer transition-all duration-300 hover:scale-[1.02] relative ${isSelected
                  ? 'border-primary bg-primary/5 shadow-md shadow-primary/10'
                  : 'border-border hover:border-primary/50 hover:shadow-sm'
                }`}
              onClick={() => handleStatusSelect(status.id)}
            >
              <div className="flex flex-col items-center text-center gap-4">
                <div className={`h-14 w-14 rounded-2xl flex items-center justify-center transition-colors ${isSelected ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground'
                  }`}>
                  <Icon className="h-7 w-7" />
                </div>
                <div>
                  <h3 className={`font-bold text-lg ${isSelected ? 'text-primary' : 'text-foreground'}`}>
                    {status.label}
                  </h3>
                  <p className="text-sm text-muted-foreground mt-1">{status.desc}</p>
                  <div className="flex items-center justify-center gap-1 mt-2 text-xs text-primary">
                    <TrendingUp className="h-3 w-3" />
                    <span className="font-semibold">{status.oppCount} opportunities</span>
                  </div>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {selectedStatus?.hasYear && academicStatus === 'undergraduate' && (
        <div className="max-w-md mx-auto animate-fade-in bg-card p-6 rounded-xl border border-border/50 shadow-sm">
          <Label className="text-base font-medium">Current Year</Label>
          <Select value={year} onValueChange={setYear}>
            <SelectTrigger className="mt-2 h-11 bg-background">
              <SelectValue placeholder="Select your year" />
            </SelectTrigger>
            <SelectContent className="bg-background border-border">
              <SelectItem value="freshman">Freshman</SelectItem>
              <SelectItem value="sophomore">Sophomore</SelectItem>
              <SelectItem value="junior">Junior</SelectItem>
              <SelectItem value="senior">Senior</SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}

      {showSchool && (
        <div className="max-w-md mx-auto space-y-6 animate-fade-in bg-card p-6 rounded-xl border border-border/50 shadow-sm">
          <div className="space-y-2">
            <Label htmlFor="school" className="text-base font-medium">Which school do you attend? (Optional)</Label>
            <Input
              id="school"
              placeholder="e.g., University of California, Berkeley"
              value={school}
              onChange={(e) => setSchool(e.target.value)}
              className="h-11 bg-background"
            />
            <p className="text-xs text-muted-foreground">
              Many opportunities are school-specific. We'll help you find them!
            </p>
          </div>

          <Button
            size="lg"
            className="w-full h-11 text-base font-medium shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all"
            onClick={handleContinue}
            disabled={!academicStatus}
          >
            Continue
          </Button>
        </div>
      )}
    </div>
  );
};

export default Step3Academic;
