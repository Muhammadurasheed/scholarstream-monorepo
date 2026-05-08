import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import type { EssayData, Scholarship } from '@/types/scholarship';

interface Step3EssaysProps {
  data: EssayData[];
  scholarship: Scholarship;
  onChange: (data: EssayData[]) => void;
  onNext: () => void;
  onPrevious: () => void;
  onSave: () => void;
  userId: string;
  scholarshipId: string;
}

export default function Step3Essays({
  data,
  scholarship,
  onChange,
  onNext,
  onPrevious,
  onSave,
}: Step3EssaysProps) {
  const prompts = scholarship.requirements.essay_prompts.length > 0
    ? scholarship.requirements.essay_prompts
    : ['Please write a personal statement describing your goals and why you deserve this scholarship. (500-750 words)'];

  const [essays, setEssays] = useState<Record<string, EssayData>>(
    data.reduce((acc, essay) => {
      acc[essay.prompt] = essay;
      return acc;
    }, {} as Record<string, EssayData>)
  );

  const [activePrompt, setActivePrompt] = useState(prompts[0]);

  useEffect(() => {
    onChange(Object.values(essays));
  }, [essays]);

  const handleContentChange = (prompt: string, content: string) => {
    const wordCount = content.trim().split(/\s+/).filter(w => w.length > 0).length;
    
    setEssays(prev => ({
      ...prev,
      [prompt]: {
        prompt,
        content,
        word_count: wordCount,
        last_edited: new Date().toISOString(),
      },
    }));
  };

  const getWordCountStatus = (count: number) => {
    if (count < 100) return { color: 'text-destructive', message: 'Too short' };
    if (count < 500) return { color: 'text-amber-500', message: 'Getting there' };
    if (count <= 750) return { color: 'text-green-500', message: 'Good length' };
    return { color: 'text-amber-500', message: 'Might be too long' };
  };

  const canContinue = prompts.every(prompt => {
    const essay = essays[prompt];
    return essay && essay.word_count >= 100;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Write Your Essay</h1>
        <p className="text-muted-foreground">Be authentic and specific. Take your time with this.</p>
      </div>

      {prompts.length > 1 ? (
        <Tabs value={activePrompt} onValueChange={setActivePrompt}>
          <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${prompts.length}, 1fr)` }}>
            {prompts.map((prompt, index) => (
              <TabsTrigger key={prompt} value={prompt}>
                Essay {index + 1}
              </TabsTrigger>
            ))}
          </TabsList>

          {prompts.map((prompt) => (
            <TabsContent key={prompt} value={prompt} className="space-y-4">
              <EssayEditor
                prompt={prompt}
                essay={essays[prompt]}
                onChange={(content) => handleContentChange(prompt, content)}
              />
            </TabsContent>
          ))}
        </Tabs>
      ) : (
        <EssayEditor
          prompt={prompts[0]}
          essay={essays[prompts[0]]}
          onChange={(content) => handleContentChange(prompts[0], content)}
        />
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
          Continue
        </Button>
      </div>
    </div>
  );
}

function EssayEditor({
  prompt,
  essay,
  onChange,
}: {
  prompt: string;
  essay?: EssayData;
  onChange: (content: string) => void;
}) {
  const wordCount = essay?.word_count || 0;
  const status = getWordCountStatus(wordCount);
  const progress = Math.min((wordCount / 750) * 100, 100);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Essay Prompt</CardTitle>
          <CardDescription className="text-base font-normal text-foreground">
            {prompt}
          </CardDescription>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Your Response</CardTitle>
            <div className="text-right">
              <p className={`text-sm font-medium ${status.color}`}>
                {wordCount} words · {status.message}
              </p>
              <Progress value={progress} className="w-32 h-2 mt-1" />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Textarea
            value={essay?.content || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Start writing your essay here..."
            className="min-h-[400px] text-base leading-relaxed"
          />
        </CardContent>
      </Card>

      <Card className="bg-purple-500/10 border-purple-500/20">
        <CardHeader>
          <CardTitle className="text-base">Writing Tips</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>• Be specific with examples and personal experiences</p>
          <p>• Show, don't just tell - use concrete details</p>
          <p>• Connect your experiences to your future goals</p>
          <p>• Proofread carefully before submitting</p>
        </CardContent>
      </Card>
    </div>
  );
}

function getWordCountStatus(count: number) {
  if (count < 100) return { color: 'text-destructive', message: 'Too short' };
  if (count < 500) return { color: 'text-amber-500', message: 'Getting there' };
  if (count <= 750) return { color: 'text-green-500', message: 'Good length' };
  return { color: 'text-amber-500', message: 'Might be too long' };
}
