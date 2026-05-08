import { User } from '../contexts/AuthContext';

/**
 * UNIFIED AUTH SYNC (Zero-Config)
 * 
 * Uses a CustomEvent dispatched on `window` that the extension's content script
 * listens for. This approach:
 * - Requires NO extension ID configuration
 * - Works across dev/prod builds without changes
 * - Fails silently if extension not installed (no errors in console)
 * 
 * Flow:
 * 1. Web app dispatches `scholarstream-auth-sync` event with token + user
 * 2. Extension content script catches it, forwards to background
 * 3. Background stores in chrome.storage.local → triggers WebSocket reconnect
 */
export const syncAuthToExtension = (token: string, user: User) => {
  try {
    const payload = {
      token,
      user: {
        uid: user.uid,
        email: user.email,
        name: user.name,
      },
    };

    // Dispatch custom event that the extension's content script listens for
    const event = new CustomEvent('scholarstream-auth-sync', {
      detail: payload,
    });
    window.dispatchEvent(event);

    console.log('🔄 [Extension Sync] Auth event dispatched');
  } catch (err) {
    // Fail silently - extension sync should never break web auth
    console.log('⚠️ [Extension Sync] Event dispatch failed (extension may not be installed)');
  }
};

/**
 * Notify extension that user has logged out
 */
export const notifyExtensionLogout = () => {
  try {
    const event = new CustomEvent('scholarstream-auth-logout');
    window.dispatchEvent(event);
    console.log('🔄 [Extension Sync] Logout event dispatched');
  } catch {
    // Fail silently
  }
};
