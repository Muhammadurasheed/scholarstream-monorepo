import { useState } from 'react';
import { Filter, ChevronDown, Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from '@/components/ui/popover';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

export type SourceScope = 'all' | 'devpost.com' | 'dorahacks.io' | 'hackquest.io' | 'scholarships.com' | 'bold.org' | 'mlh.io' | 'hackerone.com' | 'immunefi.com' | 'kaggle.com' | 'other';

interface SourceFilterProps {
    selectedSource: SourceScope;
    onSourceChange: (source: SourceScope) => void;
}

const sourceOptions: { value: SourceScope; label: string; color: string }[] = [
    { value: 'all', label: 'All Sources', color: 'bg-muted' },
    { value: 'devpost.com', label: 'DevPost', color: 'bg-[#003E54] text-white' },
    { value: 'dorahacks.io', label: 'DoraHacks', color: 'bg-[#FF761C] text-white' },
    { value: 'hackquest.io', label: 'HackQuest', color: 'bg-indigo-600 text-white' },
    { value: 'scholarships.com', label: 'Scholarships.com', color: 'bg-blue-600 text-white' },
    { value: 'bold.org', label: 'Bold.org', color: 'bg-black text-white' },
    { value: 'mlh.io', label: 'MLH', color: 'bg-red-600 text-white' },
    { value: 'hackerone.com', label: 'HackerOne', color: 'bg-slate-800 text-white' },
    { value: 'immunefi.com', label: 'Immunefi', color: 'bg-purple-700 text-white' },
    { value: 'kaggle.com', label: 'Kaggle', color: 'bg-cyan-600 text-white' },
];

export const SourceFilter = ({
    selectedSource,
    onSourceChange,
}: SourceFilterProps) => {
    const [open, setOpen] = useState(false);

    const selectedOption = sourceOptions.find(opt => opt.value === selectedSource);

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="outline"
                    size="sm"
                    className={cn(
                        'gap-2 h-9',
                        selectedSource !== 'all' && 'border-primary text-primary bg-primary/5'
                    )}
                >
                    <Filter className="h-4 w-4" />
                    <span className="hidden sm:inline">
                        {selectedOption?.label || 'Source'}
                    </span>
                    <ChevronDown className="h-3 w-3 opacity-50" />
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-56 p-1" align="start">
                <div className="space-y-1">
                    <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                        Filter by Platform
                    </div>
                    {sourceOptions.map((option) => (
                        <button
                            key={option.value}
                            onClick={() => {
                                onSourceChange(option.value);
                                setOpen(false);
                            }}
                            className={cn(
                                'w-full flex items-center justify-between px-2 py-1.5 rounded-sm text-sm transition-colors',
                                selectedSource === option.value
                                    ? 'bg-accent text-accent-foreground'
                                    : 'hover:bg-muted'
                            )}
                        >
                            <div className="flex items-center gap-2">
                                {option.value !== 'all' && (
                                    <div className={cn("w-2 h-2 rounded-full", option.color.split(' ')[0])} />
                                )}
                                <span>{option.label}</span>
                            </div>
                            {selectedSource === option.value && (
                                <Check className="h-4 w-4 text-primary" />
                            )}
                        </button>
                    ))}
                </div>
                {selectedSource !== 'all' && (
                    <>
                        <div className="my-1 h-px bg-muted" />
                        <Button
                            variant="ghost"
                            size="sm"
                            className="w-full justify-start text-xs h-8 px-2"
                            onClick={() => {
                                onSourceChange('all');
                                setOpen(false);
                            }}
                        >
                            <X className="mr-2 h-3 w-3" />
                            Clear Filter
                        </Button>
                    </>
                )}
            </PopoverContent>
        </Popover>
    );
};
