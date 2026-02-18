import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Mail, X } from 'lucide-react';
import type { RecommenderData, Scholarship } from '@/types/scholarship';

interface Step4RecommendersProps {
  data: RecommenderData[];
  scholarship: Scholarship;
  onChange: (data: RecommenderData[]) => void;
  onNext: () => void;
  onPrevious: () => void;
  onSave: () => void;
}

export default function Step4Recommenders({
  data,
  scholarship,
  onChange,
  onNext,
  onPrevious,
  onSave,
}: Step4RecommendersProps) {
  const requiredCount = scholarship.requirements.recommendation_letters;
  const [recommenders, setRecommenders] = useState<RecommenderData[]>(data);
  const [showAdd, setShowAdd] = useState(false);
  const [newRecommender, setNewRecommender] = useState<Partial<RecommenderData>>({
    status: 'not_requested',
  });

  const handleAdd = () => {
    if (newRecommender.name && newRecommender.email && newRecommender.relationship) {
      const recommender: RecommenderData = {
        name: newRecommender.name,
        email: newRecommender.email,
        relationship: newRecommender.relationship,
        subject_context: newRecommender.subject_context,
        phone: newRecommender.phone,
        status: 'not_requested',
      };
      
      const updated = [...recommenders, recommender];
      setRecommenders(updated);
      onChange(updated);
      setNewRecommender({ status: 'not_requested' });
      setShowAdd(false);
    }
  };

  const handleRemove = (index: number) => {
    const updated = recommenders.filter((_, i) => i !== index);
    setRecommenders(updated);
    onChange(updated);
  };

  const canContinue = recommenders.length >= requiredCount;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Request Recommendation Letters</h1>
        <p className="text-muted-foreground">
          This scholarship requires {requiredCount} recommendation letter{requiredCount > 1 ? 's' : ''}
        </p>
      </div>

      <Card className="bg-blue-500/10 border-blue-500/20">
        <CardContent className="pt-6">
          <h3 className="font-semibold text-foreground mb-2">Tips for Choosing Recommenders:</h3>
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li>• Choose people who know you well and can speak to your strengths</li>
            <li>• Request letters at least 3-4 weeks before the deadline</li>
            <li>• Provide context about the scholarship and why you're applying</li>
            <li>• Follow up politely if you haven't heard back in a week</li>
          </ul>
        </CardContent>
      </Card>

      {/* Existing Recommenders */}
      <div className="space-y-4">
        {recommenders.map((rec, index) => (
          <Card key={index}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-lg">{rec.name}</CardTitle>
                  <CardDescription>{rec.relationship}</CardDescription>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemove(index)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-muted-foreground">Email:</span>{' '}
                  <span className="text-foreground">{rec.email}</span>
                </div>
                {rec.subject_context && (
                  <div>
                    <span className="text-muted-foreground">Context:</span>{' '}
                    <span className="text-foreground">{rec.subject_context}</span>
                  </div>
                )}
              </div>
              <div className="flex gap-2 pt-2">
                <Button size="sm" variant="outline" className="gap-2">
                  <Mail className="h-4 w-4" />
                  Generate Request Email
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Add New Recommender */}
      {showAdd ? (
        <Card>
          <CardHeader>
            <CardTitle>Add Recommender</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="rec_name">Name *</Label>
                <Input
                  id="rec_name"
                  value={newRecommender.name || ''}
                  onChange={(e) => setNewRecommender({ ...newRecommender, name: e.target.value })}
                  placeholder="Dr. Jane Smith"
                />
              </div>

              <div>
                <Label htmlFor="rec_email">Email *</Label>
                <Input
                  id="rec_email"
                  type="email"
                  value={newRecommender.email || ''}
                  onChange={(e) => setNewRecommender({ ...newRecommender, email: e.target.value })}
                  placeholder="jane.smith@school.edu"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="rec_relationship">Relationship *</Label>
                <Select
                  value={newRecommender.relationship || ''}
                  onValueChange={(value) => setNewRecommender({ ...newRecommender, relationship: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select relationship" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="teacher">Teacher / Professor</SelectItem>
                    <SelectItem value="counselor">School Counselor</SelectItem>
                    <SelectItem value="advisor">Academic Advisor</SelectItem>
                    <SelectItem value="employer">Employer / Supervisor</SelectItem>
                    <SelectItem value="mentor">Mentor / Coach</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="rec_context">Subject/Context</Label>
                <Input
                  id="rec_context"
                  value={newRecommender.subject_context || ''}
                  onChange={(e) => setNewRecommender({ ...newRecommender, subject_context: e.target.value })}
                  placeholder="AP Computer Science, Fall 2025"
                />
              </div>
            </div>

            <div className="flex gap-2 pt-2">
              <Button onClick={handleAdd}>Add Recommender</Button>
              <Button variant="outline" onClick={() => setShowAdd(false)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Button
          variant="outline"
          className="w-full gap-2"
          onClick={() => setShowAdd(true)}
          disabled={recommenders.length >= 5}
        >
          <Plus className="h-4 w-4" />
          Add Recommender
        </Button>
      )}

      {!canContinue && (
        <Card className="bg-amber-500/10 border-amber-500/20">
          <CardContent className="pt-6">
            <p className="text-sm text-foreground">
              You need to add {requiredCount - recommenders.length} more recommender{requiredCount - recommenders.length > 1 ? 's' : ''} to continue.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Navigation */}
      <div className="flex justify-between pt-6">
        <div className="space-x-2">
          <Button variant="outline" onClick={onPrevious}>
            Previous
          </Button>
          <Button variant="ghost" onClick={onSave}>
            Save Draft
          </Button>
        </div>
        <Button onClick={onNext} size="lg" disabled={!canContinue}>
          Continue to Review
        </Button>
      </div>
    </div>
  );
}
