
import asyncio
import websockets
import structlog
import sys

logger = structlog.get_logger()

async def test_websocket_connection():
    uri = "ws://localhost:8000/ws/opportunities?token=TEST_TOKEN"
    print(f"[*] Attempting connection to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully (Unexpected with invalid token!)")
            await websocket.close()
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"[*] Server responded with status code: {e.status_code}")
        if e.status_code == 1008 or e.status_code == 403:
             print("✅ Server is reachable & Auth rejected invalid token (Expected behavior)")
        else:
             print(f"⚠️ Unexpected status code: {e.status_code}")
             
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Is the backend running on localhost:8000?")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_websocket_connection())
