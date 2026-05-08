import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const validateFirebaseConfig = () => {
  const requiredEnvVars = [
    'VITE_FIREBASE_API_KEY',
    'VITE_FIREBASE_AUTH_DOMAIN',
    'VITE_FIREBASE_PROJECT_ID',
    'VITE_FIREBASE_STORAGE_BUCKET',
    'VITE_FIREBASE_MESSAGING_SENDER_ID',
    'VITE_FIREBASE_APP_ID',
  ] as const;

  const missing = requiredEnvVars.filter((k) => !import.meta.env[k]);
  if (missing.length > 0) {
    throw new Error(
      `Firebase configuration incomplete for extension. Missing: ${missing.join(', ')}`,
    );
  }
};

// Validate configuration before initializing (prevents a blank sidepanel with cryptic errors)
console.log("[Firebase Init] Checking environment variables...");
console.log("[Firebase Init] VITE_FIREBASE_API_KEY:", import.meta.env.VITE_FIREBASE_API_KEY ? "FOUND (" + import.meta.env.VITE_FIREBASE_API_KEY.substring(0, 5) + "...)" : "MISSING");
console.log("[Firebase Init] VITE_FIREBASE_PROJECT_ID:", import.meta.env.VITE_FIREBASE_PROJECT_ID);

validateFirebaseConfig();

// Shared config with main app
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
};

let app: any;
let auth: any;
let db: any;
let initError: Error | null = null;

try {
  console.log("[Firebase Init] Attempting to initialize app...");
  app = initializeApp(firebaseConfig);

  // Initialize services
  auth = getAuth(app);
  db = getFirestore(app);

  console.log("[Firebase Init] Successfully initialized!");
} catch (error: any) {
  console.error("[Firebase Init] CRITICAL FAILURE:", error);
  initError = error;
  // Do NOT throw here, or the module evaluation fails and the app won't render.
  // We leave auth/db as undefined/proxies, and handle checks in the UI.
}

export { app, auth, db, initError };
