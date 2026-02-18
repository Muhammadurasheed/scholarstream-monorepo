import { useEffect, useState, useCallback, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from '@/hooks/use-toast';
import { Scholarship } from '@/types/scholarship';

interface WebSocketMessage {
  type: 'connection_established' | 'new_opportunity' | 'heartbeat' | 'pong';
  opportunity?: Scholarship;
  message?: string;
  timestamp: string;
}

export function useRealtimeOpportunities() {
  const { user } = useAuth();
  const [connected, setConnected] = useState(false);
  const [opportunities, setOpportunities] = useState<Scholarship[]>([]);
  // Buffer state for "Twitter-style" updates
  const [bufferedOpportunities, setBufferedOpportunities] = useState<Scholarship[]>([]);
  // Counter for new opportunities (for NotificationPill)
  const [newOpportunitiesCount, setNewOpportunitiesCount] = useState(0);
  // Track IDs that were just flushed (for highlighting)
  const [justFlushedIds, setJustFlushedIds] = useState<Set<string>>(new Set());

  // WebSocket refs
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const maxReconnectAttempts = 5;
  const flushTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Clear new count
  const clearNewOpportunitiesCount = useCallback(() => {
    setNewOpportunitiesCount(0);
  }, []);

  // Clear "just flushed" highlighting after timeout
  const clearJustFlushed = useCallback(() => {
    setJustFlushedIds(new Set());
  }, []);

  // Flush function: Moves buffered items to main list
  const flushBuffer = useCallback(() => {
    if (bufferedOpportunities.length === 0) return;

    // Track which IDs are being flushed for highlighting
    const flushedIds = new Set(bufferedOpportunities.map(o => o.id));
    setJustFlushedIds(flushedIds);

    setOpportunities(prev => [...bufferedOpportunities, ...prev]);
    setBufferedOpportunities([]);
    setNewOpportunitiesCount(0);

    // Clear the highlight after 30 seconds
    if (flushTimeoutRef.current) {
      clearTimeout(flushTimeoutRef.current);
    }
    flushTimeoutRef.current = setTimeout(() => {
      setJustFlushedIds(new Set());
    }, 30000);

    // Smooth scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [bufferedOpportunities]);

  const connect = useCallback(async () => {
    if (!user) return;

    try {
      // Use the token stored by AuthContext (user object doesn't have getIdToken method)
      const token = localStorage.getItem('scholarstream_auth_token');

      if (!token) {
        console.error('No auth token found in localStorage');
        return;
      }

      const wsUrl = import.meta.env.VITE_API_BASE_URL
        ?.replace('https://', 'wss://')
        ?.replace('http://', 'ws://');

      const ws = new WebSocket(`${wsUrl}/ws/opportunities?token=${token}`);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        reconnectAttempts.current = 0;

        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 25000);

        ws.addEventListener('close', () => {
          clearInterval(pingInterval);
        });
      };

      ws.onmessage = (event) => {
        try {
          if (!event.data) return;

          const message: WebSocketMessage = JSON.parse(event.data);

          console.log('WebSocket message received:', message.type);

          switch (message.type) {
            case 'connection_established':
              toast({
                title: '⚡ Real-Time Stream Active',
                description: 'We are scanning the web for you...',
                duration: 3000,
              });
              break;

            case 'new_opportunity':
              // Defensive check: Ensure opportunity object exists and has an ID
              if (message.opportunity && message.opportunity.id) {
                // ADD TO BUFFER INSTEAD OF MAIN LIST
                setBufferedOpportunities((prev) => {
                  // Prevent duplicates in buffer
                  if (prev.some(op => op.id === message.opportunity?.id)) return prev;
                  // Prevent duplicates in main list
                  if (opportunities.some(op => op.id === message.opportunity?.id)) return prev;

                  return [message.opportunity!, ...prev];
                });

                setNewOpportunitiesCount((count) => count + 1);

                if (message.opportunity.priority_level?.toLowerCase() === 'urgent') {
                  toast({
                    title: '🚨 Urgent Opportunity Discovered!',
                    description: `${message.opportunity.name} - Deadline approaching!`,
                    duration: 10000,
                  });
                }
              } else {
                console.warn("Received malformed opportunity message", message);
              }
              break;

            case 'heartbeat':
              // Optional: Update last seen timestamp
              break;

            case 'pong':
              break;

            default:
              console.log('Unknown message type:', message.type);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error, event.data);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setConnected(false);

        if (
          event.code !== 1000 &&
          reconnectAttempts.current < maxReconnectAttempts
        ) {
          const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30000);
          reconnectAttempts.current += 1;

          console.log(`Reconnecting in ${delay / 1000} seconds...`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          toast({
            title: 'Connection Lost',
            description:
              'Unable to connect to real-time streaming. Refresh the page to retry.',
            variant: 'destructive',
          });
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }, [user]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }

    setConnected(false);
  }, []);


  useEffect(() => {
    if (user) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [user, connect, disconnect]);

  return {
    connected,
    opportunities,
    newOpportunitiesCount,
    clearNewOpportunitiesCount,
    flushBuffer,
    justFlushedIds,
    clearJustFlushed,
    reconnect: connect,
  };
}
