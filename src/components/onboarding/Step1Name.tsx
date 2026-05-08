import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { OnboardingData } from '@/pages/Onboarding';

interface Step1Props {
  data: OnboardingData;
  onNext: (data: Partial<OnboardingData>) => void;
}

const Step1Name: React.FC<Step1Props> = ({ data, onNext }) => {
  const [firstName, setFirstName] = useState(data.firstName);
  const [lastName, setLastName] = useState(data.lastName);
  const [errors, setErrors] = useState({ firstName: '', lastName: '' });

  const validate = () => {
    const newErrors = { firstName: '', lastName: '' };

    if (!firstName.trim()) {
      newErrors.firstName = 'First name is required';
    } else if (firstName.trim().length < 2) {
      newErrors.firstName = 'Must be at least 2 characters';
    }

    if (!lastName.trim()) {
      newErrors.lastName = 'Last name is required';
    } else if (lastName.trim().length < 2) {
      newErrors.lastName = 'Must be at least 2 characters';
    }

    setErrors(newErrors);
    return !newErrors.firstName && !newErrors.lastName;
  };

  const handleContinue = () => {
    if (validate()) {
      onNext({ firstName: firstName.trim(), lastName: lastName.trim() });
    }
  };

  return (
    <div className="space-y-8 animate-slide-up">
      <div className="text-center space-y-3">
        <p className="text-sm text-primary font-semibold tracking-wide uppercase">Step 1 of 6</p>
        <h1 className="text-3xl md:text-4xl font-bold text-foreground tracking-tight">
          Let's start simple. <br />
          <span className="text-primary">What's your name?</span>
        </h1>
        <p className="text-lg text-muted-foreground max-w-lg mx-auto">
          We'll use this to personalize your scholarship journey.
        </p>
      </div>

      <div className="max-w-md mx-auto space-y-6 bg-card p-8 rounded-2xl shadow-sm border border-border/50">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="firstName" className="text-foreground/80">First Name</Label>
            <Input
              id="firstName"
              placeholder="Jane"
              value={firstName}
              onChange={(e) => {
                setFirstName(e.target.value);
                setErrors({ ...errors, firstName: '' });
              }}
              className={`h-11 ${errors.firstName ? 'border-destructive focus-visible:ring-destructive' : 'focus-visible:ring-primary'}`}
              autoFocus
            />
            {errors.firstName && (
              <p className="text-sm text-destructive font-medium">{errors.firstName}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="lastName" className="text-foreground/80">Last Name</Label>
            <Input
              id="lastName"
              placeholder="Doe"
              value={lastName}
              onChange={(e) => {
                setLastName(e.target.value);
                setErrors({ ...errors, lastName: '' });
              }}
              className={`h-11 ${errors.lastName ? 'border-destructive focus-visible:ring-destructive' : 'focus-visible:ring-primary'}`}
            />
            {errors.lastName && (
              <p className="text-sm text-destructive font-medium">{errors.lastName}</p>
            )}
          </div>
        </div>

        <Button
          size="lg"
          className="w-full h-11 text-base font-medium shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all"
          onClick={handleContinue}
          disabled={!firstName || !lastName}
        >
          Continue
        </Button>
      </div>
    </div>
  );
};

export default Step1Name;