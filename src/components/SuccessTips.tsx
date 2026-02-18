/**
 * Success Tips Component
 * FAANG-Level: Actionable advice for scholarship applications
 */
import { CheckCircle, Lightbulb, AlertCircle, Target } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface SuccessTipsProps {
    requiresEssay: boolean;
    requiresRecommendations: number;
    competitionLevel: 'Low' | 'Medium' | 'High';
    amount: number;
}

export const SuccessTips = ({
    requiresEssay,
    requiresRecommendations,
    competitionLevel,
    amount
}: SuccessTipsProps) => {
    const tips = [
        {
            icon: CheckCircle,
            title: 'Start Early',
            description: 'Give yourself at least 2-3 weeks to prepare a strong application. Last-minute submissions rarely showcase your best work.',
            color: 'text-green-600'
        },
        {
            icon: Target,
            title: 'Be Specific',
            description: 'Use concrete examples and numbers to demonstrate your achievements. Instead of "I helped my community," say "I organized 5 food drives that served 200+ families."',
            color: 'text-blue-600'
        },
        {
            icon: Lightbulb,
            title: 'Tell Your Story',
            description: requiresEssay
                ? 'Your essay should reveal who you are beyond grades. Share personal experiences that shaped your goals and values.'
                : 'Even in short answers, inject personality. Show reviewers what makes you unique.',
            color: 'text-purple-600'
        },
        {
            icon: CheckCircle,
            title: 'Proofread Thoroughly',
            description: 'Have at least 2 people review your application before submitting. Typos and errors can hurt even the strongest applications.',
            color: 'text-orange-600'
        },
    ];

    // Add competition-specific tips
    if (competitionLevel === 'High' || amount >= 10000) {
        tips.push({
            icon: Target,
            title: 'Stand Out from the Crowd',
            description: `This is a highly competitive ${amount >= 10000 ? 'high-value ' : ''}scholarship. Focus on what makes you unique. Highlight specific achievements, leadership roles, and impact you've made.`,
            color: 'text-red-600'
        });
    }

    if (requiresRecommendations > 0) {
        tips.push({
            icon: Lightbulb,
            title: 'Choose Recommenders Wisely',
            description: `Select ${requiresRecommendations} recommender(s) who know you well and can speak to specific examples of your character and achievements. Give them at least 2 weeks notice.`,
            color: 'text-indigo-600'
        });
    }

    return (
        <Card className="p-6">
            <h2 className="text-2xl font-bold mb-4">💡 Success Tips</h2>

            <div className="space-y-4 mb-6">
                {tips.map((tip, index) => {
                    const Icon = tip.icon;
                    return (
                        <div key={index} className="flex items-start gap-3">
                            <Icon className={`h-5 w-5 ${tip.color} flex-shrink-0 mt-0.5`} />
                            <div>
                                <h3 className="font-semibold mb-1">{tip.title}</h3>
                                <p className="text-sm text-muted-foreground">{tip.description}</p>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Common Mistakes Alert */}
            <Alert className="bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800">
                <AlertCircle className="h-4 w-4 text-amber-600" />
                <AlertDescription className="text-sm text-amber-900 dark:text-amber-100">
                    <strong>Common Mistakes to Avoid:</strong>
                    <ul className="mt-2 space-y-1 ml-4 list-disc">
                        <li>Submitting generic essays that could apply to any scholarship</li>
                        <li>Missing the deadline or submitting incomplete applications</li>
                        <li>Ignoring word limits or formatting requirements</li>
                        <li>Not following up to confirm all materials were received</li>
                    </ul>
                </AlertDescription>
            </Alert>
        </Card>
    );
};
