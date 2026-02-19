(base) 
HP@Emrash MINGW64 ~/Documents/scholarstream-monorepo/backend (main)
$ python run.py
[INFO] Checking Port 8081 availability...
[INFO] Port is free and bindable.
[INFO] Environment variables loaded from .env
==> Starting ScholarStream FastAPI Backend...
==> Server will run at: http://localhost:8081
==> Auto-reload DISABLED for stability
2026-02-19 12:38:41 [info     ] OpportunityScraperService: CORTEX MODE ACTIVE legacy_scrapers=REMOVED message=All discovery via Playwright-based Sentinel patrols
2026-02-19 12:38:43 [info     ] Firebase initialized successfully
2026-02-19 12:38:45 [info     ] Chat service initialized       model=gemini-2.0-flash
2026-02-19 12:38:45 [info     ] Firebase already initialized  
2026-02-19 12:38:45 [info     ] Upstash Redis initialized successfully
2026-02-19 12:38:45 [info     ] Gemini AI Service initialized  model=gemini-2.0-flash rate_limit=1000 redis_enabled=True
INFO:     Started server process [27872]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8081 (Press CTRL+C to quit)
INFO:     ('127.0.0.1', 52166) - "WebSocket /ws/opportunities?token=eyJhbGciOiJSUzI1NiIsImtpZCI6ImY1MzMwMzNhMTMzYWQyM2EyYzlhZGNmYzE4YzRlM2E3MWFmYWY2MjkiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vc2Nob2xhcnN0cmVhbS1pNGkiLCJhdWQiOiJzY2hvbGFyc3RyZWFtLWk0aSIsImF1dGhfdGltZSI6MTc2NjUyMTY4MiwidXNlcl9pZCI6IkVMM0dGS1UxdmJRWUlPNkdkRDFITmNNU0RBYjIiLCJzdWIiOiJFTDNHRktVMXZiUVlJTzZHZEQxSE5jTVNEQWIyIiwiaWF0IjoxNzcxNTAxMzUzLCJleHAiOjE3NzE1MDQ5NTMsImVtYWlsIjoib2dhbUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZW1haWwiOlsib2dhbUBnbWFpbC5jb20iXX0sInNpZ25faW5fcHJvdmlkZXIiOiJwYXNzd29yZCJ9fQ.2mAbSfzAPh21gUIkPUVs0pH3RAumrRv4OZE3wBbdUk5zf9I3c_sJLDjTvPEaW5IbRBDLNC_6vwz4nQ90ESTQUgS1ajXEdRtVjfxIy5YhjUgYYI6mFZQTwE4R1m0P7rFX8bTSTvHQGCO7sE8ZQsbV030GF0_wP6nHYhd3YCSce_zKdb1HHcGlFVg2exRIxOqLlzmPHjYlmLTxOjsOKBlTWkCQeYteA2HyV8irZyGbuaqiBqp4HmEAmP7WU5H_HFNgm0nArBhqYRVHnaZnLuqy1MBPacqQfmMfysDHpglPO3p2jqko5RXNlNEp2FxJHaaM_B_eXkC6oGijvRgLJABtSA" [accepted]     
INFO:     connection open
INFO:     127.0.0.1:62702 - "OPTIONS /api/scholarships/matched?user_id=EL3GFKU1vbQYIO6GdD1HNcMSDAb2 HTTP/1.1" 200 OK
INFO:     ('127.0.0.1', 59644) - "WebSocket /ws/opportunities?token=eyJhbGciOiJSUzI1NiIsImtpZCI6ImY1MzMwMzNhMTMzYWQyM2EyYzlhZGNmYzE4YzRlM2E3MWFmYWY2MjkiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vc2Nob2xhcnN0cmVhbS1pNGkiLCJhdWQiOiJzY2hvbGFyc3RyZWFtLWk0aSIsImF1dGhfdGltZSI6MTc2NjUyMTY4MiwidXNlcl9pZCI6IkVMM0dGS1UxdmJRWUlPNkdkRDFITmNNU0RBYjIiLCJzdWIiOiJFTDNHRktVMXZiUVlJTzZHZEQxSE5jTVNEQWIyIiwiaWF0IjoxNzcxNTAxMzUzLCJleHAiOjE3NzE1MDQ5NTMsImVtYWlsIjoib2dhbUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZW1haWwiOlsib2dhbUBnbWFpbC5jb20iXX0sInNpZ25faW5fcHJvdmlkZXIiOiJwYXNzd29yZCJ9fQ.2mAbSfzAPh21gUIkPUVs0pH3RAumrRv4OZE3wBbdUk5zf9I3c_sJLDjTvPEaW5IbRBDLNC_6vwz4nQ90ESTQUgS1ajXEdRtVjfxIy5YhjUgYYI6mFZQTwE4R1m0P7rFX8bTSTvHQGCO7sE8ZQsbV030GF0_wP6nHYhd3YCSce_zKdb1HHcGlFVg2exRIxOqLlzmPHjYlmLTxOjsOKBlTWkCQeYteA2HyV8irZyGbuaqiBqp4HmEAmP7WU5H_HFNgm0nArBhqYRVHnaZnLuqy1MBPacqQfmMfysDHpglPO3p2jqko5RXNlNEp2FxJHaaM_B_eXkC6oGijvRgLJABtSA" [accepted]     
INFO:     connection open
INFO:     127.0.0.1:62702 - "GET /api/scholarships/matched?user_id=EL3GFKU1vbQYIO6GdD1HNcMSDAb2 HTTP/1.1" 200 OK
INFO:     ('127.0.0.1', 57586) - "WebSocket /ws/opportunities?token=eyJhbGciOiJSUzI1NiIsImtpZCI6ImY1MzMwMzNhMTMzYWQyM2EyYzlhZGNmYzE4YzRlM2E3MWFmYWY2MjkiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vc2Nob2xhcnN0cmVhbS1pNGkiLCJhdWQiOiJzY2hvbGFyc3RyZWFtLWk0aSIsImF1dGhfdGltZSI6MTc2NjUyMTY4MiwidXNlcl9pZCI6IkVMM0dGS1UxdmJRWUlPNkdkRDFITmNNU0RBYjIiLCJzdWIiOiJFTDNHRktVMXZiUVlJTzZHZEQxSE5jTVNEQWIyIiwiaWF0IjoxNzcxNTAxMzUzLCJleHAiOjE3NzE1MDQ5NTMsImVtYWlsIjoib2dhbUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZW1haWwiOlsib2dhbUBnbWFpbC5jb20iXX0sInNpZ25faW5fcHJvdmlkZXIiOiJwYXNzd29yZCJ9fQ.2mAbSfzAPh21gUIkPUVs0pH3RAumrRv4OZE3wBbdUk5zf9I3c_sJLDjTvPEaW5IbRBDLNC_6vwz4nQ90ESTQUgS1ajXEdRtVjfxIy5YhjUgYYI6mFZQTwE4R1m0P7rFX8bTSTvHQGCO7sE8ZQsbV030GF0_wP6nHYhd3YCSce_zKdb1HHcGlFVg2exRIxOqLlzmPHjYlmLTxOjsOKBlTWkCQeYteA2HyV8irZyGbuaqiBqp4HmEAmP7WU5H_HFNgm0nArBhqYRVHnaZnLuqy1MBPacqQfmMfysDHpglPO3p2jqko5RXNlNEp2FxJHaaM_B_eXkC6oGijvRgLJABtSA" [accepted]     
INFO:     connection open
2026-02-19 11:43:19 [error    ] Reader LLM extraction failed   [app.services.cortex.reader_llm] error=429 Resource exhausted. Please try again later. Please refer to https://cloud.google.com/vertex-ai/generative-ai/docs/error-code-429 for more details. url=https://hackathon.io/events
2026-02-19 11:43:19 [warning  ] No opportunities extracted     [app.services.cortex.refinery] url=https://hackathon.io/events
2026-02-19 11:43:23 [error    ] Reader LLM extraction failed   [app.services.cortex.reader_llm] error=429 Resource exhausted. Please try again later. Please refer to https://cloud.google.com/vertex-ai/generative-ai/docs/error-code-429 for more details. url=https://lablab.ai/event
2026-02-19 11:43:23 [warning  ] No opportunities extracted     [app.services.cortex.refinery] url=https://lablab.ai/event
2026-02-19 11:44:35 [warning  ] No opportunities extracted     [app.services.cortex.refinery] url=https://gitcoin.co/hackathons
2026-02-19 11:44:46 [error    ] Reader LLM extraction failed   [app.services.cortex.reader_llm] error=429 Resource exhausted. Please try again later. Please refer to https://cloud.google.com/vertex-ai/generative-ai/docs/error-code-429 for more details. url=https://eventornado.com/
2026-02-19 11:44:46 [warning  ] No opportunities extracted     [app.services.cortex.refinery] url=https://eventornado.com/
2026-02-19 11:47:33 [warning  ] No opportunities extracted     [app.services.cortex.refinery] url=https://gitcoin.co/grants-stack/explorer
2026-02-19 11:47:43 [error    ] Reader LLM extraction failed   [app.services.cortex.reader_llm] error=429 Resource exhausted. Please try again later. Please refer to https://cloud.google.com/vertex-ai/generative-ai/docs/error-code-429 for more details. url=https://immunefi.com/explore
2026-02-19 11:47:43 [warning  ] No opportunities extracted     [app.services.cortex.refinery] url=https://immunefi.com/explore
2026-02-19 11:47:57 [warning  ] Content too thin, retrying     [app.services.crawler_service] length=176 url=https://dorahacks.io/api/bounty/list?status=open&page=1&limit=50
2026-02-19 11:48:08 [warning  ] Content too thin, retrying     [app.services.crawler_service] length=176 url=https://dorahacks.io/api/bounty/list?status=open&page=1&limit=50
2026-02-19 11:48:16 [error    ] Reader LLM extraction failed   [app.services.cortex.reader_llm] error=429 Resource exhausted. Please try again later. Please refer to https://cloud.google.com/vertex-ai/generative-ai/docs/error-code-429 for more details. url=https://earn.superteam.fun/bounties/
2026-02-19 11:48:16 [warning  ] No opportunities extracted     [app.services.cortex.refinery] url=https://earn.superteam.fun/bounties/
2026-02-19 11:48:19 [warning  ] Content too thin, retrying     [app.services.crawler_service] length=176 url=https://dorahacks.io/api/bounty/list?status=open&page=1&limit=50
2026-02-19 11:48:19 [error    ] Direct fetch failed after all retries [app.services.crawler_service] error=Unknown url=https://dorahacks.io/api/bounty/list?status=open&page=1&limit=50
2026-02-19 11:48:21 [error    ] Reader LLM extraction failed   [app.services.cortex.reader_llm] error=429 Resource exhausted. Please try again later. Please refer to https://cloud.google.com/vertex-ai/generative-ai/docs/error-code-429 for more details. url=https://bugcrowd.com/programs
2026-02-19 11:48:21 [warning  ] No opportunities extracted     [app.services.cortex.refinery] url=https://bugcrowd.com/programs
2026-02-19 11:48:45 [error    ] Reader LLM extraction failed   [app.services.cortex.reader_llm] error=429 Resource exhausted. Please try again later. Please refer to https://cloud.google.com/vertex-ai/generative-ai/docs/error-code-429 for more details. url=https://dorahacks.io/bounty
2026-02-19 11:48:45 [warning  ] No opportunities extracted     [app.services.cortex.refinery] url=https://dorahacks.io/bounty
2026-02-19 11:49:16 [warning  ] Drone mission aborted: 404/Not Found [app.services.crawler_service] title=404: This page could not be found. url=https://solana.com/grants
2026-02-19 11:49:23 [warning  ] Drone mission aborted: 404/Not Found [app.services.crawler_service] title=404 Error | Aave url=https://aave.com/grants/   
2026-02-19 11:49:31 [error    ] Reader LLM extraction failed   [app.services.cortex.reader_llm] error=429 Resource exhausted. Please try again later. Please refer to https://cloud.google.com/vertex-ai/generative-ai/docs/error-code-429 for more details. url=https://compound.finance/grants
2026-02-19 11:49:31 [warning  ] No opportunities extracted     [app.services.cortex.refinery] url=https://compound.finance/grants
