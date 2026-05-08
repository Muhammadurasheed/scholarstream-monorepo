import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { OnboardingData } from '@/pages/Onboarding';
import { MapPin } from 'lucide-react';

interface Step8Props {
  data: OnboardingData;
  onNext: (data: Partial<OnboardingData>) => void;
}

const countries = [
  'United States',
  'Canada',
  'United Kingdom',
  'Australia',
  'Germany',
  'France',
  'India',
  'Nigeria',
  'South Africa',
  'Brazil',
  'Mexico',
  'Other',
];

const usStates = [
  'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware',
  'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky',
  'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi',
  'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico',
  'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania',
  'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont',
  'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming',
];

const Step8Location = ({ data, onNext }: Step8Props) => {
  const [country, setCountry] = useState<string>(data.country || '');
  const [state, setState] = useState<string>(data.state || '');
  const [city, setCity] = useState<string>(data.city || '');

  const handleContinue = () => {
    onNext({ country, state, city });
  };

  const showStates = country === 'United States';

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="text-center space-y-2">
        <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
          <MapPin className="h-8 w-8 text-primary" />
        </div>
        <h2 className="text-3xl font-bold text-foreground">
          Where are you located?
        </h2>
        <p className="text-muted-foreground">
          Many opportunities are location-specific
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="country">Country *</Label>
          <Select value={country} onValueChange={setCountry}>
            <SelectTrigger id="country" className="bg-background">
              <SelectValue placeholder="Select your country" />
            </SelectTrigger>
            <SelectContent className="bg-background border-border max-h-[300px]">
              {countries.map((c) => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {showStates && (
          <div className="space-y-2 animate-fade-in">
            <Label htmlFor="state">State</Label>
            <Select value={state} onValueChange={setState}>
              <SelectTrigger id="state" className="bg-background">
                <SelectValue placeholder="Select your state" />
              </SelectTrigger>
              <SelectContent className="bg-background border-border max-h-[300px]">
                {usStates.map((s) => (
                  <SelectItem key={s} value={s}>
                    {s}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="city">City (Optional)</Label>
          <Input
            id="city"
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="Enter your city"
            className="bg-background"
          />
        </div>
      </div>

      <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
        <p className="text-sm text-foreground flex items-start gap-2">
          <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0 text-blue-400" />
          <span>
            We'll find local opportunities others miss. Many scholarships and grants are
            state or region-specific, giving you an advantage!
          </span>
        </p>
      </div>

      <Button
        onClick={handleContinue}
        disabled={!country}
        className="w-full"
        size="lg"
      >
        Continue
      </Button>
    </div>
  );
};

export default Step8Location;
