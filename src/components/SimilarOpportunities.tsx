/**
 * Similar Opportunities Component
 * FAANG-Level: Recommendation carousel based on match scores
 */
import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, ExternalLink, TrendingUp } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Scholarship } from '@/types/scholarship';
import { formatCurrency, getMatchTierColor } from '@/utils/scholarshipUtils';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface SimilarOpportunitiesProps {
    currentOpportunity: Scholarship;
    allOpportunities?: Scholarship[];
    maxItems?: number;
}

export const SimilarOpportunities = ({
    currentOpportunity,
    allOpportunities = [],
    maxItems = 6
}: SimilarOpportunitiesProps) => {
    const navigate = useNavigate();
    const [currentIndex, setCurrentIndex] = useState(0);
    const [similarOpps, setSimilarOpps] = useState<Scholarship[]>([]);

    useEffect(() => {
        // Find similar opportunities based on tags, amount, and type
        const similar = allOpportunities
            .filter(opp => opp.id !== currentOpportunity.id)
            .map(opp => {
                let similarity = 0;

                // Tag similarity (40%)
                const currentTags = new Set(currentOpportunity.tags);
                const oppTags = new Set(opp.tags);
                const commonTags = [...currentTags].filter(tag => oppTags.has(tag)).length;
                const totalTags = Math.max(currentTags.size, oppTags.size);
                similarity += (commonTags / totalTags) * 40;

                // Amount similarity (30%)
                const amountDiff = Math.abs(opp.amount - currentOpportunity.amount);
                const amountSimilarity = Math.max(0, 1 - (amountDiff / currentOpportunity.amount));
                similarity += amountSimilarity * 30;

                // Match tier similarity (20%)
                if (opp.match_tier === currentOpportunity.match_tier) {
                    similarity += 20;
                }

                // Organization similarity (10%)
                if (opp.organization === currentOpportunity.organization) {
                    similarity += 10;
                }

                return { ...opp, similarity };
            })
            .sort((a, b) => b.similarity - a.similarity)
            .slice(0, maxItems);

        setSimilarOpps(similar);
    }, [currentOpportunity, allOpportunities, maxItems]);

    const handlePrevious = () => {
        setCurrentIndex(prev => Math.max(0, prev - 1));
    };

    const handleNext = () => {
        setCurrentIndex(prev => Math.min(similarOpps.length - 3, prev + 1));
    };

    const handleViewOpportunity = (id: string) => {
        navigate(`/opportunity/${id}`);
        window.scrollTo(0, 0);
    };

    if (similarOpps.length === 0) {
        return null;
    }

    const visibleOpps = similarOpps.slice(currentIndex, currentIndex + 3);

    return (
        <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-primary" />
                    <h2 className="text-2xl font-bold">Similar Opportunities</h2>
                </div>

                <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        size="icon"
                        onClick={handlePrevious}
                        disabled={currentIndex === 0}
                        className="h-8 w-8"
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <Button
                        variant="outline"
                        size="icon"
                        onClick={handleNext}
                        disabled={currentIndex >= similarOpps.length - 3}
                        className="h-8 w-8"
                    >
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {visibleOpps.map((opp) => (
                    <Card
                        key={opp.id}
                        className="p-4 hover:shadow-lg transition-shadow cursor-pointer group"
                        onClick={() => handleViewOpportunity(opp.id)}
                    >
                        <div className="flex items-start justify-between mb-3">
                            <Badge
                                className={cn(
                                    "text-xs",
                                    getMatchTierColor(opp.match_tier)
                                )}
                            >
                                {Math.round(opp.match_score)}% Match
                            </Badge>
                            <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>

                        <h3 className="font-semibold text-sm mb-2 line-clamp-2 group-hover:text-primary transition-colors">
                            {opp.name}
                        </h3>

                        <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
                            {opp.organization}
                        </p>

                        <div className="flex items-center justify-between">
                            <span className="font-bold text-primary">
                                {formatCurrency(opp.amount)}
                            </span>
                            <Badge variant="outline" className="text-xs">
                                {opp.deadline_type}
                            </Badge>
                        </div>

                        {opp.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-3">
                                {opp.tags.slice(0, 2).map((tag, index) => (
                                    <Badge key={index} variant="secondary" className="text-xs">
                                        {tag}
                                    </Badge>
                                ))}
                                {opp.tags.length > 2 && (
                                    <Badge variant="secondary" className="text-xs">
                                        +{opp.tags.length - 2}
                                    </Badge>
                                )}
                            </div>
                        )}
                    </Card>
                ))}
            </div>

            <div className="text-center mt-4">
                <p className="text-sm text-muted-foreground">
                    Showing {currentIndex + 1}-{Math.min(currentIndex + 3, similarOpps.length)} of {similarOpps.length} similar opportunities
                </p>
            </div>
        </Card>
    );
};
