import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { GraduationCap, Code, DollarSign, Trophy, FileText } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface OpportunityTypeFilterProps {
  selectedType: string;
  onTypeChange: (type: string) => void;
  counts: {
    all: number;
    scholarship: number;
    hackathon: number;
    bounty: number;
    competition: number;
    grant: number;
  };
}

export const OpportunityTypeFilter = ({
  selectedType,
  onTypeChange,
  counts,
}: OpportunityTypeFilterProps) => {
  return (
    <Tabs value={selectedType} onValueChange={onTypeChange} className="w-full">
      <TabsList className="w-full justify-start overflow-x-auto">
        <TabsTrigger value="all" className="gap-2">
          <span>All Opportunities</span>
          <Badge variant="secondary" className="ml-1">
            {counts.all}
          </Badge>
        </TabsTrigger>
        <TabsTrigger value="scholarship" className="gap-2">
          <GraduationCap className="h-4 w-4" />
          <span>Scholarships</span>
          <Badge variant="secondary" className="ml-1">
            {counts.scholarship}
          </Badge>
        </TabsTrigger>
        <TabsTrigger value="hackathon" className="gap-2">
          <Code className="h-4 w-4" />
          <span>Hackathons</span>
          <Badge variant="secondary" className="ml-1">
            {counts.hackathon}
          </Badge>
        </TabsTrigger>
        <TabsTrigger value="bounty" className="gap-2">
          <DollarSign className="h-4 w-4" />
          <span>Bounties</span>
          <Badge variant="secondary" className="ml-1">
            {counts.bounty}
          </Badge>
        </TabsTrigger>
        <TabsTrigger value="competition" className="gap-2">
          <Trophy className="h-4 w-4" />
          <span>Competitions</span>
          <Badge variant="secondary" className="ml-1">
            {counts.competition}
          </Badge>
        </TabsTrigger>
        <TabsTrigger value="grant" className="gap-2">
          <FileText className="h-4 w-4" />
          <span>Grants</span>
          <Badge variant="secondary" className="ml-1">
            {counts.grant}
          </Badge>
        </TabsTrigger>
      </TabsList>
    </Tabs>
  );
};
