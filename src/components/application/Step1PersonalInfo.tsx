import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import type { PersonalInfoData } from '@/types/scholarship';

interface Step1PersonalInfoProps {
  data: PersonalInfoData | null;
  onChange: (data: PersonalInfoData) => void;
  onNext: () => void;
  onSave: () => void;
}

export default function Step1PersonalInfo({ data, onChange, onNext, onSave }: Step1PersonalInfoProps) {
  const { user } = useAuth();
  const [formData, setFormData] = useState<PersonalInfoData>(
    data || {
      full_name: '',
      email: user?.email || '',
      phone: '',
      mailing_address: {},
      school_name: '',
      grade_level: '',
      gpa_scale: '4.0',
      ethnicity: [],
    }
  );
  const [sameAddress, setSameAddress] = useState(true);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    onChange(formData);
  }, [formData]);

  const handleChange = (field: keyof PersonalInfoData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setErrors(prev => ({ ...prev, [field]: '' }));
  };

  const handleAddressChange = (type: 'mailing_address' | 'permanent_address', field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [type]: { ...(prev[type] || {}), [field]: value },
    }));
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.full_name.trim()) newErrors.full_name = 'Full name is required';
    if (!formData.email.trim()) newErrors.email = 'Email is required';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) newErrors.email = 'Invalid email format';
    if (!formData.phone.trim()) newErrors.phone = 'Phone number is required';
    if (!formData.school_name.trim()) newErrors.school_name = 'School name is required';
    if (!formData.grade_level) newErrors.grade_level = 'Grade level is required';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validate()) {
      if (!sameAddress && !formData.permanent_address) {
        setFormData(prev => ({ ...prev, permanent_address: { ...prev.mailing_address } }));
      }
      onNext();
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Tell Us About Yourself</h1>
        <p className="text-muted-foreground">Most of this information is pre-filled from your profile</p>
      </div>

      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
          <CardDescription>Your personal details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="full_name">Full Legal Name *</Label>
              <Input
                id="full_name"
                value={formData.full_name}
                onChange={(e) => handleChange('full_name', e.target.value)}
                placeholder="John Michael Doe"
              />
              {errors.full_name && <p className="text-sm text-destructive mt-1">{errors.full_name}</p>}
            </div>

            <div>
              <Label htmlFor="preferred_name">Preferred Name (if different)</Label>
              <Input
                id="preferred_name"
                value={formData.preferred_name || ''}
                onChange={(e) => handleChange('preferred_name', e.target.value)}
                placeholder="Mike"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="email">Email Address *</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                placeholder="john.doe@example.com"
              />
              {errors.email && <p className="text-sm text-destructive mt-1">{errors.email}</p>}
            </div>

            <div>
              <Label htmlFor="phone">Phone Number *</Label>
              <Input
                id="phone"
                type="tel"
                value={formData.phone}
                onChange={(e) => handleChange('phone', e.target.value)}
                placeholder="(555) 123-4567"
              />
              {errors.phone && <p className="text-sm text-destructive mt-1">{errors.phone}</p>}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="date_of_birth">Date of Birth</Label>
              <Input
                id="date_of_birth"
                type="date"
                value={formData.date_of_birth || ''}
                onChange={(e) => handleChange('date_of_birth', e.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="gender">Gender (Optional)</Label>
              <Select value={formData.gender || ''} onValueChange={(value) => handleChange('gender', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select gender" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="male">Male</SelectItem>
                  <SelectItem value="female">Female</SelectItem>
                  <SelectItem value="non-binary">Non-binary</SelectItem>
                  <SelectItem value="prefer-not-to-say">Prefer not to say</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Address Information */}
      <Card>
        <CardHeader>
          <CardTitle>Address Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-4">
            <h3 className="font-semibold text-foreground">Mailing Address</h3>
            
            <div>
              <Label htmlFor="street">Street Address</Label>
              <Input
                id="street"
                value={formData.mailing_address.street || ''}
                onChange={(e) => handleAddressChange('mailing_address', 'street', e.target.value)}
                placeholder="123 Main St"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="city">City</Label>
                <Input
                  id="city"
                  value={formData.mailing_address.city || ''}
                  onChange={(e) => handleAddressChange('mailing_address', 'city', e.target.value)}
                  placeholder="Anytown"
                />
              </div>

              <div>
                <Label htmlFor="state">State</Label>
                <Input
                  id="state"
                  value={formData.mailing_address.state || ''}
                  onChange={(e) => handleAddressChange('mailing_address', 'state', e.target.value)}
                  placeholder="CA"
                />
              </div>

              <div>
                <Label htmlFor="zip">ZIP Code</Label>
                <Input
                  id="zip"
                  value={formData.mailing_address.zip || ''}
                  onChange={(e) => handleAddressChange('mailing_address', 'zip', e.target.value)}
                  placeholder="12345"
                />
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="sameAddress"
              checked={sameAddress}
              onCheckedChange={(checked) => setSameAddress(checked as boolean)}
            />
            <Label htmlFor="sameAddress" className="text-sm cursor-pointer">
              Permanent address is the same as mailing address
            </Label>
          </div>
        </CardContent>
      </Card>

      {/* Academic Information */}
      <Card>
        <CardHeader>
          <CardTitle>Academic Information</CardTitle>
          <CardDescription>From your profile</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="school_name">School Name *</Label>
              <Input
                id="school_name"
                value={formData.school_name}
                onChange={(e) => handleChange('school_name', e.target.value)}
                placeholder="University of Example"
              />
              {errors.school_name && <p className="text-sm text-destructive mt-1">{errors.school_name}</p>}
            </div>

            <div>
              <Label htmlFor="student_id">Student ID</Label>
              <Input
                id="student_id"
                value={formData.student_id || ''}
                onChange={(e) => handleChange('student_id', e.target.value)}
                placeholder="123456789"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="grade_level">Grade Level *</Label>
              <Select value={formData.grade_level} onValueChange={(value) => handleChange('grade_level', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select grade level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="freshman">Freshman</SelectItem>
                  <SelectItem value="sophomore">Sophomore</SelectItem>
                  <SelectItem value="junior">Junior</SelectItem>
                  <SelectItem value="senior">Senior</SelectItem>
                  <SelectItem value="graduate">Graduate Student</SelectItem>
                </SelectContent>
              </Select>
              {errors.grade_level && <p className="text-sm text-destructive mt-1">{errors.grade_level}</p>}
            </div>

            <div>
              <Label htmlFor="major">Major / Field of Study</Label>
              <Input
                id="major"
                value={formData.major || ''}
                onChange={(e) => handleChange('major', e.target.value)}
                placeholder="Computer Science"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="gpa">Current GPA</Label>
              <Input
                id="gpa"
                type="number"
                step="0.01"
                value={formData.gpa || ''}
                onChange={(e) => handleChange('gpa', parseFloat(e.target.value))}
                placeholder="3.5"
              />
            </div>

            <div>
              <Label htmlFor="gpa_scale">GPA Scale</Label>
              <Select value={formData.gpa_scale} onValueChange={(value) => handleChange('gpa_scale', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="4.0">4.0 Scale</SelectItem>
                  <SelectItem value="5.0">5.0 Scale</SelectItem>
                  <SelectItem value="100">100-Point Scale</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="expected_graduation">Expected Graduation</Label>
              <Input
                id="expected_graduation"
                type="month"
                value={formData.expected_graduation || ''}
                onChange={(e) => handleChange('expected_graduation', e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between pt-6">
        <Button variant="ghost" onClick={onSave}>
          Save Draft
        </Button>
        <Button onClick={handleNext} size="lg">
          Continue
        </Button>
      </div>
    </div>
  );
}
