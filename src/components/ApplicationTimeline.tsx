/**
 * Application Timeline Component
 * FAANG-Level: Step-by-step guide for scholarship applications
 */
import { CheckCircle, Circle, Clock } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface TimelineStep {
    week: string;
    title: string;
    description: string;
    tasks: string[];
    completed?: boolean;
}

interface ApplicationTimelineProps {
    requiresEssay: boolean;
    requiresRecommendations: number;
    requiresTranscript: boolean;
    deadlineType: 'rolling' | 'fixed';
}

export const ApplicationTimeline = ({
    requiresEssay,
    requiresRecommendations,
    requiresTranscript,
    deadlineType
}: ApplicationTimelineProps) => {
    const steps: TimelineStep[] = [
        {
            week: 'Week 1-2',
            title: 'Gather Materials',
            description: 'Collect all required documents and information',
            tasks: [
                requiresTranscript ? 'Request official transcript from your school' : 'Prepare unofficial transcript',
                'Update your resume with recent achievements',
                requiresRecommendations > 0 ? `Identify ${requiresRecommendations} recommender(s)` : 'Review application requirements',
                'Gather proof of enrollment or acceptance letter',
            ].filter(Boolean),
        },
        {
            week: 'Week 2-3',
            title: requiresEssay ? 'Draft Essays' : 'Prepare Application',
            description: requiresEssay
                ? 'Write compelling essays that showcase your story'
                : 'Fill out application forms carefully',
            tasks: requiresEssay ? [
                'Brainstorm essay topics and create outlines',
                'Write first drafts for all required essays',
                'Get feedback from teachers or mentors',
                'Revise and polish your essays',
            ] : [
                'Fill out personal information accurately',
                'Double-check all dates and details',
                'Prepare short answer responses',
                'Review application for completeness',
            ],
        },
        {
            week: 'Week 3-4',
            title: 'Finalize & Submit',
            description: 'Review everything and submit before deadline',
            tasks: [
                'Proofread all materials one final time',
                'Have 2-3 people review your complete application',
                requiresRecommendations > 0 ? 'Confirm recommendation letters are submitted' : 'Verify all documents are attached',
                'Submit application at least 48 hours before deadline',
                'Save confirmation email and application copy',
            ].filter(Boolean),
        },
    ];

    return (
        <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold">📅 Application Timeline</h2>
                {deadlineType === 'rolling' && (
                    <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                        Rolling Deadline - Apply Anytime
                    </Badge>
                )}
            </div>

            <div className="space-y-6">
                {steps.map((step, index) => (
                    <div key={index} className="relative">
                        {/* Connector Line */}
                        {index < steps.length - 1 && (
                            <div className="absolute left-4 top-12 bottom-0 w-0.5 bg-gradient-to-b from-primary/50 to-primary/20" />
                        )}

                        <div className="flex gap-4">
                            {/* Step Icon */}
                            <div className={cn(
                                "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
                                "bg-primary/10 text-primary border-2 border-primary/30"
                            )}>
                                <span className="text-sm font-bold">{index + 1}</span>
                            </div>

                            {/* Step Content */}
                            <div className="flex-1 pb-8">
                                <div className="flex items-center gap-2 mb-2">
                                    <Badge variant="secondary" className="text-xs">
                                        {step.week}
                                    </Badge>
                                    <h3 className="font-semibold text-lg">{step.title}</h3>
                                </div>

                                <p className="text-sm text-muted-foreground mb-3">
                                    {step.description}
                                </p>

                                <ul className="space-y-2">
                                    {step.tasks.map((task, taskIndex) => (
                                        <li key={taskIndex} className="flex items-start gap-2 text-sm">
                                            <Circle className="h-4 w-4 text-primary/40 flex-shrink-0 mt-0.5" />
                                            <span>{task}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Pro Tips */}
            <div className="mt-6 p-4 bg-amber-50 dark:bg-amber-950/20 rounded-lg border border-amber-200 dark:border-amber-800">
                <div className="flex items-start gap-2">
                    <Clock className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div>
                        <p className="font-semibold text-amber-900 dark:text-amber-100 mb-1">
                            Pro Tip: Start Early
                        </p>
                        <p className="text-sm text-amber-800 dark:text-amber-200">
                            Give yourself at least 3-4 weeks to prepare a strong application.
                            Last-minute applications rarely showcase your best work.
                        </p>
                    </div>
                </div>
            </div>
        </Card>
    );
};
