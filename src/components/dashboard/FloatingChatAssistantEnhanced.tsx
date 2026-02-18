import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Sparkles, Loader2, Bookmark, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import ssLogo from '@/asset/ss_logo.png';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import { Scholarship } from '@/types/scholarship';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  opportunities?: Scholarship[];
  timestamp: string;
}

export const FloatingChatAssistantEnhanced = () => {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hi! I'm your ScholarStream AI assistant. I can help you:\n\n• Find opportunities matching your needs\n• Answer questions about scholarships\n• Help with applications\n• Give deadline reminders\n\nTry asking: 'Find urgent opportunities' or 'Show me hackathons this week'",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [savedOpportunities, setSavedOpportunities] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const quickPrompts = [
    'Find urgent opportunities',
    'Scholarships for my major',
    'Hackathons this week',
    'High-value scholarships',
  ];

  const handleSend = async (message?: string) => {
    const messageText = message || input.trim();
    if (!messageText || !user) return;

    const userMessage: Message = {
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081';
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.uid,
          message: messageText,
          context: {
            current_page: window.location.pathname,
            timestamp: new Date().toISOString(),
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();

      const assistantMessage: Message = {
        role: 'assistant',
        content: data.message || 'I found some opportunities for you!',
        opportunities: data.opportunities || [],
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Show toast if opportunities found
      if (data.opportunities && data.opportunities.length > 0) {
        toast.success(`Found ${data.opportunities.length} opportunities!`);
      }
    } catch (error) {
      console.error('Chat error:', error);

      const errorMessage: Message = {
        role: 'assistant',
        content: 'I\'m having trouble right now. Please try again in a moment, or browse your dashboard.',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);

      toast.error('Failed to get response. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickPrompt = (prompt: string) => {
    handleSend(prompt);
  };

  const handleSaveOpportunity = (oppId: string) => {
    setSavedOpportunities(prev => {
      const next = new Set(prev);
      if (next.has(oppId)) {
        next.delete(oppId);
        toast.success('Removed from favorites');
      } else {
        next.add(oppId);
        toast.success('Saved to favorites');
      }
      return next;
    });
  };

  const handleViewOpportunity = (oppId: string) => {
    window.open(`/opportunity/${oppId}`, '_blank');
  };

  if (!isOpen) {
    return (
      <Button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 h-16 w-16 rounded-full shadow-2xl hover:scale-110 transition-transform bg-transparent p-0 z-50 overflow-hidden"
        size="icon"
      >
        <img src={ssLogo} alt="AI Assistant" className="h-full w-full object-cover" />
      </Button>
    );
  }

  return (
    <Card className="fixed bottom-6 right-6 w-[min(450px,calc(100vw-3rem))] h-[min(650px,calc(100vh-8rem))] flex flex-col shadow-2xl border-primary/20 animate-in slide-in-from-bottom-4 z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-primary/10 to-primary/5">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 text-primary-foreground flex items-center justify-center">
            <img src={ssLogo} alt="AI Logo" className="h-10 w-10 object-contain" />
          </div>
          <div>
            <h3 className="font-semibold">ScholarStream AI</h3>
            <p className="text-xs text-muted-foreground">Always here to help</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsOpen(false)}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl p-3 ${message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
                  }`}
              >
                <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>

                {/* Opportunity Cards */}
                {message.opportunities && message.opportunities.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {message.opportunities.slice(0, 5).map((opp) => (
                      <Card key={opp.id} className="p-3 bg-background hover:shadow-md transition-shadow">
                        <div className="space-y-2">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1 flex-wrap">
                                <Badge variant="secondary" className="text-xs">
                                  {opp.source_type}
                                </Badge>
                                {opp.priority_level === 'urgent' && (
                                  <Badge variant="destructive" className="text-xs animate-pulse">
                                    Urgent
                                  </Badge>
                                )}
                                <Badge variant="outline" className="text-xs">
                                  {opp.match_score}% match
                                </Badge>
                              </div>
                              <h4 className="font-semibold text-sm line-clamp-2 mb-1">{opp.name}</h4>
                              <p className="text-xs text-muted-foreground">{opp.organization}</p>
                            </div>
                          </div>

                          <div className="flex items-center gap-3 text-xs">
                            <span className="font-semibold text-primary">
                              {opp.amount_display}
                            </span>
                            {opp.deadline && (
                              <span className="text-muted-foreground">
                                Due: {new Date(opp.deadline).toLocaleDateString()}
                              </span>
                            )}
                          </div>

                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              className="flex-1 h-8 text-xs gap-1"
                              onClick={() => handleViewOpportunity(opp.id)}
                            >
                              <ExternalLink className="h-3 w-3" />
                              View
                            </Button>
                            <Button
                              size="sm"
                              variant={savedOpportunities.has(opp.id) ? 'default' : 'outline'}
                              className="h-8 w-8 p-0"
                              onClick={() => handleSaveOpportunity(opp.id)}
                            >
                              <Bookmark className={`h-3 w-3 ${savedOpportunities.has(opp.id) ? 'fill-current' : ''}`} />
                            </Button>
                          </div>
                        </div>
                      </Card>
                    ))}
                    {message.opportunities.length > 5 && (
                      <p className="text-xs text-center text-muted-foreground pt-2">
                        +{message.opportunities.length - 5} more opportunities
                      </p>
                    )}
                  </div>
                )}

                <p className="text-xs text-muted-foreground/60 mt-2">
                  {new Date(message.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-muted rounded-2xl p-3 flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm text-muted-foreground">Thinking...</span>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Quick Prompts */}
      {messages.length <= 1 && !isLoading && (
        <div className="px-4 pb-2">
          <div className="flex flex-wrap gap-2">
            {quickPrompts.map((prompt) => (
              <Button
                key={prompt}
                variant="outline"
                size="sm"
                className="text-xs h-8"
                onClick={() => handleQuickPrompt(prompt)}
              >
                {prompt}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t bg-background">
        <div className="flex gap-2">
          <Input
            placeholder="Ask anything..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !isLoading && handleSend()}
            disabled={isLoading}
            className="flex-1"
          />
          <Button
            size="icon"
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2 text-center">
          AI can make mistakes. Verify important information.
        </p>
      </div>
    </Card>
  );
};
