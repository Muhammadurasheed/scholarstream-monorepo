import { useEffect, useRef } from 'react';
import { doc, setDoc } from 'firebase/firestore';
import { db } from '@/lib/firebase';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { sanitizeData } from '@/lib/utils';

export const useFirebaseAutoSave = <T extends Record<string, any>>(
  data: T,
  collectionPath: string,
  debounceMs: number = 1000
) => {
  const { user } = useAuth();
  const { toast } = useToast();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0);
  const MAX_RETRIES = 3;

  useEffect(() => {
    if (!user) return;

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set new timeout for debounced save
    timeoutRef.current = setTimeout(async () => {
      try {
        const docRef = doc(db, collectionPath, user.uid);
        const cleanData = sanitizeData(data);

        await setDoc(docRef, {
          ...cleanData,
          updated_at: new Date(),
        }, { merge: true });

        retryCountRef.current = 0; // Reset retry count on success

        // Save to localStorage as backup
        localStorage.setItem(`${collectionPath}_backup`, JSON.stringify(data));
      } catch (error: any) {
        // Don't retry if permission denied
        if (error.code === 'permission-denied') {
          console.warn('Firebase auto-save permission denied. Check Firestore rules.');
          return;
        }

        console.error('Firebase auto-save failed:', error);

        // Retry logic
        if (retryCountRef.current < MAX_RETRIES) {
          retryCountRef.current++;
          console.log(`Retrying save (${retryCountRef.current}/${MAX_RETRIES})...`);

          // Retry after exponential backoff
          setTimeout(() => {
            timeoutRef.current = setTimeout(async () => {
              try {
                const docRef = doc(db, collectionPath, user.uid);
                const cleanData = sanitizeData(data);
                await setDoc(docRef, {
                  ...cleanData,
                  updated_at: new Date(),
                }, { merge: true });
                retryCountRef.current = 0;
              } catch (retryError) {
                console.error('Retry failed:', retryError);
              }
            }, 0);
          }, Math.pow(2, retryCountRef.current) * 1000);
        } else {
          // Show warning after max retries
          toast({
            title: 'Auto-save issue',
            description: 'Progress saved locally. Will sync when connection improves.',
            variant: 'default',
          });

          // Save to localStorage as fallback
          localStorage.setItem(`${collectionPath}_backup`, JSON.stringify(data));
        }
      }
    }, debounceMs);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [data, user, collectionPath, debounceMs, toast]);
};
