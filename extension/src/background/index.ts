
// Background Service Worker for ScholarStream Co-Pilot
// Handles Push Notifications via WebSocket with REAL Firebase Auth

// API Configuration
const API_URL = 'https://scholarstream-backend-opdnpd6bsq-uc.a.run.app';
/*
const API_URL = '__VITE_API_URL__' !== '__VITE_API_URL__'
    ? '__VITE_API_URL__'
    : 'http://localhost:8081';
*/
const WS_URL = API_URL.replace('http', 'ws') + '/ws/opportunities';

let websocket: WebSocket | null = null;
let reconnectInterval = 1000;
let currentAuthToken: string | null = null;

// Initialize on install
chrome.runtime.onInstalled.addListener(() => {
    console.log("ScholarStream Co-Pilot Installed");
    initializeAuth();
});

// Also run on startup
chrome.runtime.onStartup.addListener(() => {
    console.log("ScholarStream Co-Pilot Started");
    initializeAuth();
});

// Configure Side Panel behavior
chrome.sidePanel
    .setPanelBehavior({ openPanelOnActionClick: true })
    .catch((error) => console.error(error));

// Listen for messages from Content Script or Side Panel
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'OPEN_SIDE_PANEL') {
        if (sender.tab && sender.tab.windowId) {
            chrome.sidePanel.open({ windowId: sender.tab.windowId })
                .catch((error) => console.error("Failed to open panel:", error));
        }
    }
});

// Listen for auth token changes from content script
chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName === 'local' && changes.authToken) {
        const newToken = changes.authToken.newValue;
        if (newToken && newToken !== currentAuthToken) {
            console.log('🔑 [BG] New auth token received, reconnecting WebSocket...');
            currentAuthToken = newToken;
            reconnectWithNewToken();
        }
    }
});

// --- Unified Auth Listener (Web App -> Extension) ---
chrome.runtime.onMessageExternal.addListener((message, sender, sendResponse) => {
    // 1. Security Check: Validate Sender Origin
    const allowedOrigins = [
        'http://localhost:8081',
        'http://localhost:8080',
        'http://localhost:5173',
        'https://scholarstream.app',
    ];

    const origin = sender.url ? new URL(sender.url).origin : '';
    if (!allowedOrigins.includes(origin)) {
        console.warn(`[Auth] Blocked message from unauthorized origin: ${origin}`);
        return; // Ignore unauthorized messages
    }

    // 2. Handle Sync Message
    if (message.type === 'SYNC_AUTH' && message.token) {
        console.log(`[Auth] Received Token from ${origin}`);

        // Save to storage (triggers the onChanged listener above)
        chrome.storage.local.set({
            authToken: message.token,
            userProfile: message.user || {}
        }, () => {
            console.log("[Auth] Token synced to storage!");
            sendResponse({ success: true });
        });

        // Return true to indicate async response
        return true;
    }
});

// --- Auth Initialization ---
async function initializeAuth() {
    // Try to get stored token
    const result = await chrome.storage.local.get(['authToken']);
    if (result.authToken) {
        currentAuthToken = result.authToken;
        console.log('🔑 [BG] Found existing auth token');
        connectWebSocket();
    } else {
        console.log('⚠️ [BG] No auth token found. Please log in to ScholarStream web app first.');
        // Still try to connect - will fail but user will see the error
        // connectWebSocket(); // Commented out to avoid spam
    }
}

function reconnectWithNewToken() {
    if (websocket) {
        websocket.close();
        websocket = null;
    }
    reconnectInterval = 1000;
    connectWebSocket();
}

// --- WebSocket Logic ---
function connectWebSocket() {
    if (!currentAuthToken) {
        console.log('⚠️ [WS] Cannot connect - no auth token. Please log in to ScholarStream.');
        return;
    }

    if (websocket && (websocket.readyState === WebSocket.OPEN || websocket.readyState === WebSocket.CONNECTING)) {
        return;
    }

    console.log(`[WS] Connecting to ${WS_URL} with real token...`);
    websocket = new WebSocket(`${WS_URL}?token=${currentAuthToken}`);

    websocket.onopen = () => {
        console.log("[WS] ✅ Connected with real Firebase auth!");
        reconnectInterval = 1000;
    };

    websocket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (e) {
            console.error("[WS] Parse error:", e);
        }
    };

    websocket.onclose = () => {
        console.log("[WS] Disconnected. Reconnecting...");
        websocket = null;
        setTimeout(connectWebSocket, reconnectInterval);
        reconnectInterval = Math.min(reconnectInterval * 2, 30000);
    };

    websocket.onerror = (error) => {
        console.error("[WS] Error:", error);
    };
}

function handleWebSocketMessage(message: any) {
    console.log("[WS] Received:", message);

    if (message.type === 'new_opportunity') {
        const opp = message.opportunity;
        showNotification(opp);
    }
}

function showNotification(opportunity: any) {
    const notificationId = `opp_${opportunity.id || Date.now()}`;

    chrome.notifications.create(notificationId, {
        type: 'basic',
        iconUrl: 'icons/icon128.png',
        title: 'New Scholarship Match! 🎯',
        message: `${opportunity.name}\nMatch Score: ${opportunity.match_score}%`,
        priority: 2,
        buttons: [{ title: 'View' }, { title: 'Dismiss' }]
    });

    chrome.notifications.onButtonClicked.addListener((notifId, btnIdx) => {
        if (notifId === notificationId && btnIdx === 0) {
            chrome.tabs.create({ url: opportunity.url || 'http://localhost:5173/dashboard' });
        }
    });
}

// Keep-alive for Service Worker
self.setInterval(() => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({ type: 'ping' }));
    }
}, 20000);

// Initial Auth Check
initializeAuth();
