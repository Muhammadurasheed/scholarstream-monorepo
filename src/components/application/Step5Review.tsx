import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Check, AlertTriangle, FileText, Edit } from 'lucide-react';
import type { Scholarship, PersonalInfoData, DocumentData, EssayData, RecommenderData } from '@/types/scholarship';

interface Step5ReviewProps {
  scholarship: Scholarship;
  personalInfo: PersonalInfoData | null;
  documents: DocumentData[];
  essays: EssayData[];
  recommenders: RecommenderData[];
  onEdit: (step: number) => void;
  onSubmit: (certifications: Record<string, boolean>) => void;
  onPrevious: () => void;
}

export default function Step5Review({
  scholarship,
  personalInfo,
  documents,
  essays,
  recommenders,
  onEdit,
  onSubmit,
  onPrevious,
}: Step5ReviewProps) {
  const [certifications, setCertifications] = useState({
    reviewed: false,
    proofread: false,
    truthful: false,
    final: false,
  });
  const [showConfirm, setShowConfirm] = useState(false);

  const requiredDocs = [];
  if (scholarship.requirements.transcript) requiredDocs.push('transcript');
  if (scholarship.requirements.resume) requiredDocs.push('resume');

  const allDocsUploaded = requiredDocs.every(type => 
    documents.some(d => d.document_type === type)
  );

  const allEssaysComplete = scholarship.requirements.essay
    ? essays.length > 0 && essays.every(e => e.word_count >= 100)
    : true;

  const allRecommendersAdded = recommenders.length >= scholarship.requirements.recommendation_letters;

  const isComplete = allDocsUploaded && allEssaysComplete && allRecommendersAdded && personalInfo;
  const allCertified = Object.values(certifications).every(Boolean);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Review Your Application</h1>
        <p className="text-muted-foreground">Double-check everything before submitting</p>
      </div>

      {/* Completeness Check */}
      <Card className={isComplete ? 'bg-green-500/10 border-green-500/20' : 'bg-amber-500/10 border-amber-500/20'}>
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            {isComplete ? (
              <Check className="h-6 w-6 text-green-500 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="h-6 w-6 text-amber-500 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <h3 className="font-semibold text-foreground mb-2">
                {isComplete ? '✓ Your application is ready to submit!' : '⚠️ Application incomplete'}
              </h3>
              <div className="space-y-1 text-sm">
                <CompletionItem completed={!!personalInfo} label="Personal information" />
                <CompletionItem completed={allDocsUploaded} label="Required documents" />
                <CompletionItem completed={allEssaysComplete} label="Essays" />
                <CompletionItem completed={allRecommendersAdded} label="Recommendation letters" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Personal Information */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Personal Information</CardTitle>
              <CardDescription>{personalInfo?.full_name}</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={() => onEdit(1)}>
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Button>
          </div>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Email:</span>{' '}
            <span className="text-foreground">{personalInfo?.email}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Phone:</span>{' '}
            <span className="text-foreground">{personalInfo?.phone}</span>
          </div>
          <div>
            <span className="text-muted-foreground">School:</span>{' '}
            <span className="text-foreground">{personalInfo?.school_name}</span>
          </div>
          <div>
            <span className="text-muted-foreground">GPA:</span>{' '}
            <span className="text-foreground">{personalInfo?.gpa || 'Not specified'}</span>
          </div>
        </CardContent>
      </Card>

      {/* Documents */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Documents ({documents.length} uploaded)</CardTitle>
            <Button variant="outline" size="sm" onClick={() => onEdit(2)}>
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {documents.map((doc, index) => (
            <div key={index} className="flex items-center gap-3 p-3 bg-muted rounded-lg">
              <FileText className="h-5 w-5 text-blue-500" />
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">{doc.document_type}</p>
                <p className="text-xs text-muted-foreground">{doc.file_name}</p>
              </div>
              <Check className="h-5 w-5 text-green-500" />
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Essays */}
      {essays.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Essays ({essays.length})</CardTitle>
              <Button variant="outline" size="sm" onClick={() => onEdit(3)}>
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {essays.map((essay, index) => (
              <div key={index} className="p-3 bg-muted rounded-lg">
                <p className="text-sm font-medium text-foreground mb-2">{essay.prompt}</p>
                <p className="text-xs text-muted-foreground">{essay.word_count} words</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Recommenders */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Recommendation Letters ({recommenders.length})</CardTitle>
            <Button variant="outline" size="sm" onClick={() => onEdit(4)}>
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {recommenders.map((rec, index) => (
            <div key={index} className="flex items-center gap-3 p-3 bg-muted rounded-lg">
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">{rec.name}</p>
                <p className="text-xs text-muted-foreground">{rec.relationship}</p>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Certifications */}
      <Card>
        <CardHeader>
          <CardTitle>Final Checklist</CardTitle>
          <CardDescription>Please confirm the following before submitting</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start space-x-3">
            <Checkbox
              id="reviewed"
              checked={certifications.reviewed}
              onCheckedChange={(checked) =>
                setCertifications({ ...certifications, reviewed: checked as boolean })
              }
            />
            <Label htmlFor="reviewed" className="text-sm cursor-pointer leading-relaxed">
              I have reviewed all information for accuracy
            </Label>
          </div>

          <div className="flex items-start space-x-3">
            <Checkbox
              id="proofread"
              checked={certifications.proofread}
              onCheckedChange={(checked) =>
                setCertifications({ ...certifications, proofread: checked as boolean })
              }
            />
            <Label htmlFor="proofread" className="text-sm cursor-pointer leading-relaxed">
              I have proofread my essays and documents
            </Label>
          </div>

          <div className="flex items-start space-x-3">
            <Checkbox
              id="truthful"
              checked={certifications.truthful}
              onCheckedChange={(checked) =>
                setCertifications({ ...certifications, truthful: checked as boolean })
              }
            />
            <Label htmlFor="truthful" className="text-sm cursor-pointer leading-relaxed">
              I certify that all information provided is truthful and accurate
            </Label>
          </div>

          <div className="flex items-start space-x-3">
            <Checkbox
              id="final"
              checked={certifications.final}
              onCheckedChange={(checked) =>
                setCertifications({ ...certifications, final: checked as boolean })
              }
            />
            <Label htmlFor="final" className="text-sm cursor-pointer leading-relaxed">
              I understand that submission is final and cannot be edited
            </Label>
          </div>
        </CardContent>
      </Card>

      {showConfirm && (
        <Alert>
          <AlertDescription>
            <p className="font-semibold mb-2">Are you ready to submit?</p>
            <p className="text-sm text-muted-foreground mb-4">
              Once submitted, you cannot edit your application. Deadline: {new Date(scholarship.deadline).toLocaleDateString()}
            </p>
            <div className="flex gap-2">
              <Button onClick={() => onSubmit(certifications)} disabled={!allCertified}>
                Yes, Submit Application
              </Button>
              <Button variant="outline" onClick={() => setShowConfirm(false)}>
                Go Back
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Navigation */}
      <div className="flex justify-between pt-6">
        <Button variant="outline" onClick={onPrevious}>
          Previous
        </Button>
        <Button
          onClick={() => setShowConfirm(true)}
          size="lg"
          disabled={!isComplete || !allCertified}
          className="bg-green-600 hover:bg-green-700"
        >
          Submit Application
        </Button>
      </div>
    </div>
  );
}

function CompletionItem({ completed, label }: { completed: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2">
      {completed ? (
        <Check className="h-4 w-4 text-green-500" />
      ) : (
        <div className="h-4 w-4 rounded-full border-2 border-muted-foreground" />
      )}
      <span className={completed ? 'text-foreground' : 'text-muted-foreground'}>{label}</span>
    </div>
  );
}
