import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut as firebaseSignOut,
  onIdTokenChanged,
  User as FirebaseUser
} from 'firebase/auth';
import { doc, setDoc, getDoc } from 'firebase/firestore';
import { auth, db } from '@/lib/firebase';
import { syncAuthToExtension, notifyExtensionLogout } from '@/utils/extensionSync';

export interface User {
  uid: string;
  email: string;
  name?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signUp: (email: string, password: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  isOnboardingComplete: () => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log('🔄 [AUTH] Initializing auth state listener...');

    // Listen to Firebase auth state changes AND token refreshes
    const unsubscribe = onIdTokenChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        console.log('✅ [AUTH] User authenticated:', {
          uid: firebaseUser.uid,
          email: firebaseUser.email,
        });

        // Always set user ASAP so routing/redirects don't get blocked by optional work.
        const nextUser: User = {
          uid: firebaseUser.uid,
          email: firebaseUser.email || '',
          name: firebaseUser.displayName || undefined,
        };
        setUser(nextUser);

        // Export Firebase ID Token for Extension access (best-effort)
        try {
          const idToken = await firebaseUser.getIdToken();
          localStorage.setItem('scholarstream_auth_token', idToken);
          window.dispatchEvent(new Event('storage'));
          console.log('🔑 [AUTH] Token exported to localStorage for extension');

          // --- UNIFIED AUTH SYNC (best-effort, must never break web auth) ---
          syncAuthToExtension(idToken, nextUser);
        } catch (error) {
          console.warn('⚠️ [AUTH] Token export / extension sync skipped:', error);
        }

        // Fetch user profile from Firestore to check onboarding status (best-effort)
        try {
          const userDoc = await getDoc(doc(db, 'users', firebaseUser.uid));
          const firestoreUser = userDoc.data();

          // Sync localStorage with Firestore truth
          if (firestoreUser?.onboarding_completed) {
            localStorage.setItem('scholarstream_onboarding_complete', 'true');
          } else if (firestoreUser && firestoreUser.onboarding_completed === false) {
            // Only clear if Firestore EXPLICITLY says onboarding is not complete
            // (i.e. the document exists and the field is explicitly false)
            localStorage.removeItem('scholarstream_onboarding_complete');
          }
          // If document doesn't exist yet (new Google sign-in, etc.),
          // preserve whatever is in localStorage — don't destroy it.
        } catch (error) {
          // CRITICAL: Do NOT clear localStorage on Firestore failure.
          // Preserve cached onboarding state so user isn't forced to re-onboard.
          console.warn('⚠️ [AUTH] Firestore profile check failed (non-blocking, preserving cache):', error);
        }
      } else {
        console.log('👤 [AUTH] No authenticated user');
        setUser(null);
        localStorage.removeItem('scholarstream_onboarding_complete');
      }
      setLoading(false);
    });
    return () => {
      console.log('🔄 [AUTH] Cleaning up auth listener');
      unsubscribe();
    };
  }, []);

  const signUp = async (email: string, password: string) => {
    try {
      console.log('🔐 [SIGNUP] Starting signup process...', { email });

      // Step 1: Create Firebase Auth user with emailRedirectTo
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const { uid, email: userEmail } = userCredential.user;

      console.log('✅ [SIGNUP] Firebase Auth user created successfully', { uid, email: userEmail });

      // Step 2: Try to create user document in Firestore (non-blocking)
      try {
        console.log('📝 [SIGNUP] Creating user document in Firestore...');
        await setDoc(doc(db, 'users', uid), {
          uid,
          email: userEmail,
          created_at: new Date(),
          onboarding_completed: false,
          profile: null,
        });
        console.log('✅ [SIGNUP] User document created in Firestore successfully');
      } catch (firestoreError: any) {
        // Log Firestore error but don't fail the signup
        console.warn('⚠️ [SIGNUP] Firestore write failed (non-critical):', {
          code: firestoreError.code,
          message: firestoreError.message
        });
        console.warn('⚠️ [SIGNUP] User authentication successful, but Firestore rules may need to be configured');
        console.warn('📚 [SIGNUP] See FIRESTORE_RULES.md for setup instructions');
      }

      localStorage.removeItem('scholarstream_onboarding_complete');
      console.log('✅ [SIGNUP] Signup process completed successfully');

    } catch (error: any) {
      console.error('❌ [SIGNUP] Signup failed:', {
        code: error.code,
        message: error.message,
        fullError: error
      });

      // Parse Firebase error codes to user-friendly messages
      const errorMessages: { [key: string]: string } = {
        'auth/email-already-in-use': 'This email is already registered. Please login instead.',
        'auth/invalid-email': 'Please enter a valid email address.',
        'auth/operation-not-allowed': 'Email/password accounts are not enabled. Please contact support.',
        'auth/weak-password': 'Please choose a stronger password (at least 6 characters).',
        'auth/api-key-not-valid': '⚠️ Firebase is not configured correctly. Please check your .env file and ensure all Firebase credentials are set.',
        'auth/configuration-not-found': '⚠️ Firebase configuration is missing. Please set up your .env file with Firebase credentials.',
      };

      const userMessage = errorMessages[error.code] || error.message || 'Failed to create account. Please try again.';
      throw new Error(userMessage);
    }
  };

  const signIn = async (email: string, password: string) => {
    try {
      console.log('🔐 [SIGNIN] Starting signin process...', { email });
      await signInWithEmailAndPassword(auth, email, password);
      console.log('✅ [SIGNIN] Signed in successfully', { email });
    } catch (error: any) {
      console.error('❌ [SIGNIN] Signin failed:', {
        code: error.code,
        message: error.message
      });

      const errorMessages: { [key: string]: string } = {
        'auth/user-not-found': 'No account found with this email.',
        'auth/wrong-password': 'Incorrect password. Please try again.',
        'auth/invalid-email': 'Please enter a valid email address.',
        'auth/user-disabled': 'This account has been disabled.',
        'auth/too-many-requests': 'Too many failed attempts. Please try again later.',
        'auth/invalid-credential': 'Invalid email or password. Please try again.',
        'auth/api-key-not-valid': '⚠️ Firebase is not configured correctly. Please check your .env file.',
      };

      const userMessage = errorMessages[error.code] || error.message || 'Failed to sign in. Please try again.';
      throw new Error(userMessage);
    }
  };

  const signOut = async () => {
    try {
      console.log('🚪 [SIGNOUT] Signing out...');
      await firebaseSignOut(auth);
      localStorage.removeItem('scholarstream_onboarding_complete');
      localStorage.removeItem('scholarstream_auth_token');

      // Notify extension of logout
      notifyExtensionLogout();

      console.log('✅ [SIGNOUT] Signed out successfully');
    } catch (error: any) {
      console.error('❌ [SIGNOUT] Signout failed:', {
        code: error.code,
        message: error.message
      });
      throw new Error(error.message || 'Failed to sign out');
    }
  };

  const isOnboardingComplete = () => {
    return localStorage.getItem('scholarstream_onboarding_complete') === 'true';
  };

  return (
    <AuthContext.Provider value={{ user, loading, signUp, signIn, signOut, isOnboardingComplete }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};