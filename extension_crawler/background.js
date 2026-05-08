
// Sentinel Background Worker
// Connects to Backend as a "Crawler Node"

const BACKEND_WS = 'ws://localhost:8000/ws/crawler';
const NODE_ID = 'sentinel_' + Math.random().toString(36).substr(2, 9);
let websocket = null;

function connect() {
    // 1. Idempotency Check: Don't connect if already connected
    if (websocket && (websocket.readyState === WebSocket.OPEN || websocket.readyState === WebSocket.CONNECTING)) {
        console.log("[Sentinel] Already connected or connecting. Skipping.");
        return;
    }

    console.log(`[Sentinel] Connecting as ${NODE_ID}...`);
    websocket = new WebSocket(BACKEND_WS);

    websocket.onopen = () => {
        console.log("[Sentinel] Connected to Command Center");
        chrome.action.setBadgeText({ text: "ON" });
        chrome.action.setBadgeBackgroundColor({ color: "#22c55e" });

        // Register Node
        websocket.send(JSON.stringify({
            type: 'register',
            node_id: NODE_ID,
            capabilities: ['http', 'browser']
        }));
    };

    websocket.onmessage = async (event) => {
        const msg = JSON.parse(event.data);
        console.log("[Sentinel] Command received:", msg);

        if (msg.type === 'crawl_request') {
            await executeCrawl(msg.url, msg.job_id);
        }
    };

    websocket.onclose = () => {
        console.log("[Sentinel] Disconnected");
        chrome.action.setBadgeText({ text: "OFF" });
        chrome.action.setBadgeBackgroundColor({ color: "#ef4444" });
        setTimeout(connect, 5000);
    };

    websocket.onerror = (err) => console.error("[Sentinel] Error:", err);
}

async function executeCrawl(url, jobId) {
    console.log(`[Sentinel] Crawling ${url}...`);
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Cache-Control': 'no-cache'
            }
        });

        const text = await response.text();

        // Send success back to HQ
        websocket.send(JSON.stringify({
            type: 'crawl_result',
            job_id: jobId,
            url: url,
            status: response.status,
            html: text, // Send full HTML back
            node_id: NODE_ID
        }));

        console.log(`[Sentinel] Job ${jobId} Complete. Size: ${text.length}`);
    } catch (error) {
        console.error(`[Sentinel] Job ${jobId} Failed:`, error);

        websocket.send(JSON.stringify({
            type: 'crawl_error',
            job_id: jobId,
            url: url,
            error: error.message,
            node_id: NODE_ID
        }));
    }
}

// Keep Alive Strategy: Chrome Alarms (MV3 Standard)
chrome.alarms.create('keepAlive', { periodInMinutes: 0.5 }); // Check every 30s

chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'keepAlive') {
        connect(); // Re-trigger connection logic if dead
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({ type: 'heartbeat' }));
        }
    }
});

// Initial Connection
connect();
