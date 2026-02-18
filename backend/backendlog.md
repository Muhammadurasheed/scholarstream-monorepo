HP@Emrash MINGW64 ~/Documents/scholarstream-monorepo/backend (main)
$ python run.py
[INFO] Checking Port 8081 availability...
[INFO] Port is free and bindable.
[INFO] Environment variables loaded from .env
==> Starting ScholarStream FastAPI Backend...
==> Server will run at: http://localhost:8081
==> Auto-reload DISABLED for stability
2026-02-18 10:09:26 [info     ] OpportunityScraperService: CORTEX MODE ACTIVE legacy_scrapers=REMOVED message=All discovery via Playwright-based Sentinel patrols
2026-02-18 10:09:28 [info     ] Firebase initialized successfully
2026-02-18 10:09:35 [info     ] Chat service initialized       model=gemini-2.0-flash
2026-02-18 10:09:35 [info     ] Firebase already initialized  
2026-02-18 10:09:35 [info     ] Upstash Redis initialized successfully
2026-02-18 10:09:35 [info     ] Gemini AI Service initialized  model=gemini-2.0-flash rate_limit=1000 redis_enabled=True
INFO:     Started server process [17364]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8081 (Press CTRL+C to quit)
2026-02-18 09:11:10 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:11:12 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:11:12 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:11:12 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:11:15 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:11:29 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:11:31 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:11:31 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:11:35 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:11:38 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:12:04 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:12:07 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:12:10 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:13:36 [warning  ] Content too thin, retrying     [app.services.crawler_service] length=176 url=https://dorahacks.io/api/bounty/list?status=open&page=1&limit=50
2026-02-18 09:13:47 [warning  ] Content too thin, retrying     [app.services.crawler_service] length=176 url=https://dorahacks.io/api/bounty/list?status=open&page=1&limit=50
2026-02-18 09:13:59 [warning  ] Content too thin, retrying     [app.services.crawler_service] length=176 url=https://dorahacks.io/api/bounty/list?status=open&page=1&limit=50
2026-02-18 09:13:59 [error    ] Direct fetch failed after all retries [app.services.crawler_service] error=Unknown url=https://dorahacks.io/api/bounty/list?status=open&page=1&limit=50
2026-02-18 09:14:36 [error    ] Drone crash                    [app.services.crawler_service] error=Page.goto: net::ERR_CONNECTION_TIMED_OUT at https://gitcoin.co/hackathons
Call log:
  - navigating to "https://gitcoin.co/hackathons", waiting until "commit"
 url=https://gitcoin.co/hackathons
2026-02-18 09:14:36 [error    ] Drone crash                    [app.services.crawler_service] error=Page.goto: net::ERR_CONNECTION_TIMED_OUT at https://gitcoin.co/grants-stack/explorer
Call log:
  - navigating to "https://gitcoin.co/grants-stack/explorer", waiting until "commit"
 url=https://gitcoin.co/grants-stack/explorer
2026-02-18 09:14:50 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:14:50 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:14:54 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:15:12 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:15:21 [error    ] Drone crash                    [app.services.crawler_service] error=Page.goto: net::ERR_CONNECTION_TIMED_OUT at https://intigriti.com/researchers/bug-bounty-programs
Call log:
  - navigating to "https://intigriti.com/researchers/bug-bounty-programs", waiting until "commit"
 url=https://intigriti.com/researchers/bug-bounty-programs
2026-02-18 09:15:38 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:15:38 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:15:39 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:15:40 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:15:48 [warning  ] All load strategies failed     [app.services.crawler_service] attempt=1 url=https://gitcoin.co/api/v0.1/grants/?page=1&limit=50
2026-02-18 09:16:50 [error    ] Drone crash                    [app.services.crawler_service] error=Page.goto: net::ERR_CONNECTION_TIMED_OUT at https://questbook.xyz/
Call log:
  - navigating to "https://questbook.xyz/", waiting until "commit"
 url=https://questbook.xyz/
2026-02-18 09:17:01 [warning  ] All load strategies failed     [app.services.crawler_service] attempt=2 url=https://gitcoin.co/api/v0.1/grants/?page=1&limit=50
2026-02-18 09:17:03 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:17:04 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:17:05 [warning  ] Drone mission aborted: 404/Not Found [app.services.crawler_service] title=404 Error | Aave url=https://aave.com/grants/
2026-02-18 09:17:06 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:17:36 [error    ] Drone crash                    [app.services.crawler_service] error=Page.goto: net::ERR_CONNECTION_TIMED_OUT at https://solana.com/grants
Call log:
  - navigating to "https://solana.com/grants", waiting until "commit"
 url=https://solana.com/grants
2026-02-18 09:17:50 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:17:50 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:17:50 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:18:05 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:18:14 [warning  ] All load strategies failed     [app.services.crawler_service] attempt=3 url=https://gitcoin.co/api/v0.1/grants/?page=1&limit=50
2026-02-18 09:18:14 [error    ] Direct fetch failed after all retries [app.services.crawler_service] error=Page.goto: Timeout 30000ms exceeded.
Call log:
  - navigating to "https://gitcoin.co/api/v0.1/grants/?page=1&limit=50", waiting until "commit"
 url=https://gitcoin.co/api/v0.1/grants/?page=1&limit=50
2026-02-18 09:18:22 [error    ] Drone crash                    [app.services.crawler_service] error=Page.goto: net::ERR_CONNECTION_TIMED_OUT at https://near.org/grants/
Call log:
  - navigating to "https://near.org/grants/", waiting until "commit"
 url=https://near.org/grants/
2026-02-18 09:19:15 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:19:16 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:19:17 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:19:17 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:19:33 [error    ] Drone crash                    [app.services.crawler_service] error=Page.goto: net::ERR_CONNECTION_TIMED_OUT at https://bold.org/scholarships/
Call log:
  - navigating to "https://bold.org/scholarships/", waiting until "commit"   
 url=https://bold.org/scholarships/
2026-02-18 09:19:49 [warning  ] Drone mission aborted: Content too thin (Potential Loading Shell) [app.services.crawler_service] size=754 url=https://www.goingmerry.com/scholarships
2026-02-18 09:19:53 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:19:54 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:19:55 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:19:59 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:20:14 [warning  ] Drone mission aborted: Content too thin (Potential Loading Shell) [app.services.crawler_service] size=1509 url=https://wellfound.com/role/l/internship/software-engineer
2026-02-18 09:20:16 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:20:18 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
2026-02-18 09:20:22 [error    ] EventHandler failed            [app.infrastructure.memory_broker] error='NoneType' object has no attribute 'get' handler=handle_raw_html_event
