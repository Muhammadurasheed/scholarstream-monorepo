import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { apiService } from '@/services/api';
import { toast } from 'sonner';
import { ArrowLeft, X, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { Scholarship, ApplicationDraft, PersonalInfoData, DocumentData, EssayData, RecommenderData } from '@/types/scholarship';

// Step Components (will create separately)
import Step1PersonalInfo from '@/components/application/Step1PersonalInfo';
import Step2Documents from '@/components/application/Step2Documents';
import Step3Essays from '@/components/application/Step3Essays';
import Step4Recommenders from '@/components/application/Step4Recommenders';
import Step5Review from '@/components/application/Step5Review';
import Step6Success from '@/components/application/Step6Success';

export default function Apply() {
  const { scholarshipId } = useParams<{ scholarshipId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [scholarship, setScholarship] = useState<Scholarship | null>(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [applicationId, setApplicationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  // Application Data State
  const [personalInfo, setPersonalInfo] = useState<PersonalInfoData | null>(null);
  const [documents, setDocuments] = useState<DocumentData[]>([]);
  const [essays, setEssays] = useState<EssayData[]>([]);
  const [recommenders, setRecommenders] = useState<RecommenderData[]>([]);
  const [additionalAnswers, setAdditionalAnswers] = useState<Record<string, any>>({});
  const [confirmationNumber, setConfirmationNumber] = useState<string | null>(null);

  const totalSteps = 6;
  const progress = ((currentStep - 1) / (totalSteps - 1)) * 100;

  const steps = [
    { number: 1, name: 'Personal Info', completed: currentStep > 1 },
    { number: 2, name: 'Documents', completed: currentStep > 2 },
    { number: 3, name: 'Essays', completed: currentStep > 3 },
    { number: 4, name: 'Recommendations', completed: currentStep > 4 },
    { number: 5, name: 'Review', completed: currentStep > 5 },
    { number: 6, name: 'Submit', completed: currentStep > 6 },
  ];

  // Load scholarship and check for existing draft
  useEffect(() => {
    if (!user || !scholarshipId) return;

    const loadData = async () => {
      try {
        setLoading(true);

        // Load scholarship details
        const scholarshipData = await apiService.getScholarshipById(scholarshipId);
        setScholarship(scholarshipData);

        // Check for existing draft
        const draftResponse = await apiService.getDraft(user.uid, scholarshipId);
        
        if (draftResponse.exists && draftResponse.draft) {
          const draft = draftResponse.draft;
          setApplicationId(draft.application_id);
          setCurrentStep(draft.current_step);
          setPersonalInfo(draft.personal_info || null);
          setDocuments(draft.documents || []);
          setEssays(draft.essays || []);
          setRecommenders(draft.recommenders || []);
          setAdditionalAnswers(draft.additional_answers || {});
          setLastSaved(new Date(draft.last_saved));
          
          toast.success('Draft loaded', {
            description: 'Continuing from where you left off',
          });
        } else {
          // Start new application
          const startResponse = await apiService.startApplication(user.uid, scholarshipId);
          setApplicationId(startResponse.application_id);
        }
      } catch (error) {
        console.error('Failed to load application:', error);
        toast.error('Failed to load application');
        navigate('/dashboard');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [user, scholarshipId, navigate]);

  // Auto-save functionality
  const autoSave = async () => {
    if (!user || !scholarshipId || !applicationId) return;

    try {
      setSaving(true);
      
      const response = await apiService.saveDraft(user.uid, scholarshipId, {
        current_step: currentStep,
        progress_percentage: progress,
        personal_info: personalInfo || undefined,
        documents: documents.length > 0 ? documents : undefined,
        essays: essays.length > 0 ? essays : undefined,
        recommenders: recommenders.length > 0 ? recommenders : undefined,
        additional_answers: Object.keys(additionalAnswers).length > 0 ? additionalAnswers : undefined,
      });

      setLastSaved(new Date(response.last_saved));
    } catch (error) {
      console.error('Auto-save failed:', error);
      // Don't show error toast for auto-save failures, just log
    } finally {
      setSaving(false);
    }
  };

  // Auto-save every 10 seconds when data changes
  useEffect(() => {
    const timer = setTimeout(() => {
      autoSave();
    }, 10000);

    return () => clearTimeout(timer);
  }, [personalInfo, documents, essays, recommenders, additionalAnswers, currentStep]);

  // Manual save
  const handleSave = async () => {
    await autoSave();
    toast.success('Progress saved');
  };

  // Navigation
  const handleNext = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
      autoSave();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1 && currentStep < 6) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleExit = () => {
    if (window.confirm('Your progress is saved. Exit application?')) {
      navigate(`/opportunity/${scholarshipId}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading application...</p>
        </div>
      </div>
    );
  }

  if (!scholarship) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Alert variant="destructive" className="max-w-md">
          <AlertDescription>
            Scholarship not found. Please try again.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (currentStep === 6 && confirmationNumber) {
    return (
      <Step6Success
        scholarship={scholarship}
        confirmationNumber={confirmationNumber}
        applicationId={applicationId!}
      />
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Progress Bar */}
      <div className="fixed top-0 left-0 right-0 z-50 bg-card border-b">
        <Progress value={progress} className="h-1 rounded-none" />
        
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between py-3">
            {/* Exit Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleExit}
              className="gap-2"
            >
              <X className="h-4 w-4" />
              Exit
            </Button>

            {/* Scholarship Info */}
            <div className="flex items-center gap-3">
              {scholarship.logo_url && (
                <img
                  src={scholarship.logo_url}
                  alt={scholarship.organization}
                  className="h-8 w-8 rounded object-contain"
                />
              )}
              <div className="text-sm">
                <p className="font-semibold text-foreground">{scholarship.name}</p>
                <p className="text-muted-foreground">{scholarship.amount_display}</p>
              </div>
            </div>

            {/* Auto-save Indicator */}
            <div className="text-sm text-muted-foreground">
              {saving ? (
                <span className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
                  Saving...
                </span>
              ) : lastSaved ? (
                <span className="flex items-center gap-2">
                  <Check className="h-3 w-3 text-green-500" />
                  Saved {lastSaved.toLocaleTimeString()}
                </span>
              ) : null}
            </div>
          </div>

          {/* Step Indicator */}
          <div className="flex items-center gap-2 pb-3 overflow-x-auto">
            {steps.map((step, index) => (
              <div key={step.number} className="flex items-center">
                <button
                  onClick={() => step.completed && setCurrentStep(step.number)}
                  disabled={!step.completed && step.number !== currentStep}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors ${
                    step.number === currentStep
                      ? 'bg-primary text-primary-foreground font-medium'
                      : step.completed
                      ? 'bg-green-500/20 text-green-600 hover:bg-green-500/30 cursor-pointer'
                      : 'bg-muted text-muted-foreground cursor-not-allowed'
                  }`}
                >
                  {step.completed ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <span className="flex items-center justify-center h-4 w-4 text-xs">
                      {step.number}
                    </span>
                  )}
                  <span className="hidden sm:inline">{step.name}</span>
                </button>
                {index < steps.length - 1 && (
                  <div className="h-px w-4 bg-border mx-1" />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="pt-32 pb-24 px-4">
        <div className="container mx-auto max-w-4xl">
          {currentStep === 1 && (
            <Step1PersonalInfo
              data={personalInfo}
              onChange={setPersonalInfo}
              onNext={handleNext}
              onSave={handleSave}
            />
          )}
          
          {currentStep === 2 && (
            <Step2Documents
              data={documents}
              scholarship={scholarship}
              onChange={setDocuments}
              onNext={handleNext}
              onPrevious={handlePrevious}
              onSave={handleSave}
              userId={user?.uid || ''}
              scholarshipId={scholarshipId || ''}
            />
          )}

          {currentStep === 3 && (
            <Step3Essays
              data={essays}
              scholarship={scholarship}
              onChange={setEssays}
              onNext={handleNext}
              onPrevious={handlePrevious}
              onSave={handleSave}
              userId={user?.uid || ''}
              scholarshipId={scholarshipId || ''}
            />
          )}

          {currentStep === 4 && (
            <Step4Recommenders
              data={recommenders}
              scholarship={scholarship}
              onChange={setRecommenders}
              onNext={handleNext}
              onPrevious={handlePrevious}
              onSave={handleSave}
            />
          )}

          {currentStep === 5 && (
            <Step5Review
              scholarship={scholarship}
              personalInfo={personalInfo}
              documents={documents}
              essays={essays}
              recommenders={recommenders}
              onEdit={(step) => setCurrentStep(step)}
              onSubmit={async (certifications) => {
                try {
                  const response = await apiService.submitApplication({
                    user_id: user?.uid,
                    scholarship_id: scholarshipId,
                    scholarship_name: scholarship.name,
                    scholarship_amount: scholarship.amount,
                    personal_info: personalInfo,
                    documents,
                    essays,
                    recommenders,
                    additional_answers: additionalAnswers,
                    certifications,
                  });

                  setConfirmationNumber(response.confirmation_number);
                  setCurrentStep(6);
                  toast.success('Application submitted successfully! 🎉');
                } catch (error) {
                  console.error('Submission failed:', error);
                  toast.error('Failed to submit application. Please try again.');
                }
              }}
              onPrevious={handlePrevious}
            />
          )}
        </div>
      </div>
    </div>
  );
}
