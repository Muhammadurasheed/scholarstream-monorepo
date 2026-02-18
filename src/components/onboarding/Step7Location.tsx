import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { MapPin } from 'lucide-react';

interface Step7LocationProps {
  data: {
    country?: string;
    state?: string;
    city?: string;
  };
  onNext: (data: { country: string; state?: string; city?: string }) => void;
  onBack: () => void;
}

const countries = [
  'United States',
  'Canada',
  'United Kingdom',
  'Australia',
  'India',
  'Germany',
  'France',
  'Other'
];

const usStates = [
  'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
  'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
  'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
  'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
  'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
  'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
  'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
  'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
  'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
  'West Virginia', 'Wisconsin', 'Wyoming'
];

const Step7Location = ({ data, onNext, onBack }: Step7LocationProps) => {
  const [country, setCountry] = useState(data.country || '');
  const [state, setState] = useState(data.state || '');
  const [city, setCity] = useState(data.city || '');

  const handleNext = () => {
    if (!country) return;
    onNext({ country, state, city });
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
      <div className="text-center space-y-2">
        <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 mb-4">
          <MapPin className="h-8 w-8 text-primary" />
        </div>
        <h2 className="text-3xl font-bold">Where are you located?</h2>
        <p className="text-muted-foreground text-lg">
          Many opportunities are location-specific. We'll find local scholarships others miss.
        </p>
      </div>

      <div className="space-y-4 max-w-md mx-auto">
        <div className="space-y-2">
          <Label htmlFor="country" className="text-base">
            Country <span className="text-destructive">*</span>
          </Label>
          <Select value={country} onValueChange={setCountry}>
            <SelectTrigger id="country" className="h-12">
              <SelectValue placeholder="Select your country" />
            </SelectTrigger>
            <SelectContent>
              {countries.map((c) => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {country === 'United States' && (
          <div className="space-y-2 animate-in fade-in slide-in-from-bottom-2">
            <Label htmlFor="state" className="text-base">
              State (Optional)
            </Label>
            <Select value={state} onValueChange={setState}>
              <SelectTrigger id="state" className="h-12">
                <SelectValue placeholder="Select your state" />
              </SelectTrigger>
              <SelectContent className="max-h-[300px]">
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
          <Label htmlFor="city" className="text-base">
            City (Optional)
          </Label>
          <Input
            id="city"
            placeholder="e.g., San Francisco"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="h-12"
          />
        </div>

        <div className="bg-muted/50 border border-border rounded-lg p-4 space-y-2">
          <p className="text-sm font-medium">💡 Why location matters</p>
          <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
            <li>State-specific scholarships (often $5K-$20K)</li>
            <li>Local community grants</li>
            <li>Regional hackathons and events</li>
            <li>City-based opportunities</li>
          </ul>
        </div>
      </div>

      <div className="flex justify-between pt-4">
        <Button variant="outline" onClick={onBack} size="lg">
          Back
        </Button>
        <Button
          onClick={handleNext}
          disabled={!country}
          size="lg"
          className="min-w-32"
        >
          Continue
        </Button>
      </div>
    </div>
  );
};

export default Step7Location;
