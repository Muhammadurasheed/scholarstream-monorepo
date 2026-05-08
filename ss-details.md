<p align="center">
  <img src="https://img.shields.io/badge/DevDash_2026-Sprint_to_Solution-6C63FF?style=for-the-badge" alt="DevDash 2026"/>
  <img src="https://img.shields.io/badge/Google_Cloud-Vertex_AI-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white" alt="Google Cloud"/>
  <img src="https://img.shields.io/badge/AI--Powered-Opportunity_Hub-FF6B6B?style=for-the-badge" alt="AI Powered"/>
</p>

<h1 align="center">ScholarStream</h1>

<h3 align="center">
  <em>The World's First AI-Powered Financial Opportunity Hub</em>
</h3>

<p align="center">
  <strong>$2.9 billion in scholarships go unclaimed every year.</strong><br/>
  Not because students don't deserve them — but because they never knew they existed.
</p>

---

## Inspiration

> **March 2025. Everything fell apart.**

My name is Rasheed. I'm a Petroleum Engineering student at the University of Ibadan, Nigeria. I was supposed to graduate on December 13th, 2025 — five years of work, a 3.4 GPA, Google Developer Student Clubs Mobile Lead, volunteer instructor. On paper, I checked every box.

Then my family's income dropped 60% overnight. I watched my school fee deadline come and go. I sat at home while my classmates attended lectures. And on graduation day, I wasn't on that stage with them.

Here's the part that still keeps me up at night: **I had the skills to earn the money I needed the entire time.** I've been shipping code in React and Python since 2022. But I didn't know DevPost existed. I'd never heard of Bug bounties. I had no idea that students like me were winning $10,000+ in weekend hackathons. Not because these opportunities were hidden — they were right there, scattered across dozens of platforms I'd never encountered, with deadlines silently passing me by.

The moment I stumbled onto this ecosystem, something broke inside me. Not anger at any one person, but frustration at a system-level failure: **information asymmetry**.

### The Numbers Tell The Story

| The Reality | Scale |
|---|---|
| Scholarships unclaimed annually | **$2.9 billion** (U.S. Dept. of Education) |
| Hackathon/bounty prizes scattered across the web | **Billions more**, fragmented across 10,000+ platforms |
| Students who miss life-changing opportunities | **Tens of millions**, because no one told them in time |

If I — a GDSC Lead who'd been coding for three years — didn't know, how many others are watching their futures slip away right now?

**ScholarStream exists because I refuse to let another student go through what I did.** It's not a project I built. It's a promise I made.

---

## What ScholarStream Does

Let me be blunt: ScholarStream is **not** another scholarship database. There are hundreds of those. You search, you scroll, you maybe find something, you realize the deadline was last week. That model is broken.

ScholarStream is something fundamentally different. It's an **AI-powered financial opportunity hub** — an always-on system that hunts the web for scholarships, hackathons, bounties, and grants, figures out which ones are perfect for *you* specifically, and puts them in front of you before the deadlines pass. And then it helps you actually *win* them.

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>The Problem: The Urgency Gap</h3>
      <p>
        A student in Lagos doesn't know there's a <strong>$50,000 hackathon</strong> on DevPost that perfectly matches their React skills — <em>deadline tomorrow</em>.
      </p>
      <p>
        A first-generation student in Atlanta doesn't know about a scholarship designed specifically for their background — <em>applications close in 3 days</em>.
      </p>
      <p>
        Traditional platforms are passive. They wait for you to search. But when you need $500 by Friday, you don't have time to dig through a static database.
      </p>
    </td>
    <td width="50%" valign="top">
      <h3>The Solution: Intelligence That Comes to You</h3>
      <p><strong>ScholarStream is your always-on opportunity radar:</strong></p>
      <ol>
        <li>🔍 <strong>Discovers</strong> opportunities continuously from 10+ platforms using stealth crawlers</li>
        <li>🧠 <strong>Understands</strong> them using Gemini AI — extracting deadlines, eligibility, prize amounts from raw HTML</li>
        <li>🎯 <strong>Matches</strong> them to your unique profile using 768-dimensional semantic embeddings</li>
        <li>⚡ <strong>Delivers</strong> them to your dashboard in real-time via WebSocket</li>
        <li>✨ <strong>Helps you win</strong> with an AI Co-Pilot Chrome Extension that fills out applications for you</li>
      </ol>
    </td>
  </tr>
</table>

---

## How I Built It

I won't sugarcoat this — building ScholarStream was one of the hardest things I've done. Every platform I tried to crawl blocked me. Every AI model hallucinated on messy HTML. Every architectural decision had real trade-offs. But I'm genuinely proud of where it ended up. Let me walk you through the system, piece by piece.

---

### The Blueprint: Intelligent Onboarding

Before ScholarStream finds you a single opportunity, it needs to understand *who you are* — not just your name and GPA, but your story.

Our onboarding flow captures what I call your **Digital DNA**:

| What We Capture | Why It Matters |
|---|---|
| **Hard Skills** | React, Python, Technical Writing — what you can actually do |
| **Soft Skills & Passions** | Leadership, community building — what drives you |
| **Demographics** | First-generation student, country, background — eligibility factors |
| **Academic Profile** | Major, GPA, year — qualification filters |
| **Urgency Signal** | "Tuition due in 30 days" — time-sensitivity prioritization |

But here's where it gets interesting. We don't just store this as text. Google's **`embedding-001`** model converts your entire profile into a **768-dimensional semantic vector** — what we call your Digital DNA. This means a "Petroleum Engineering student who codes in Python and cares about sustainability" semantically matches with "Energy & Climate Tech Hackathons" — a connection that keyword search would miss completely.

---

### The Scouts: Stealth Crawler Fleet

This is where the engineering challenge really began. Our first attempt at crawling opportunity platforms was... humbling.

| Attempt | What We Tried | What Happened |
|---|---|---|
| 1 | `requests` / `httpx` | Blocked immediately. 403 everywhere. |
| 2 | `Scrapy` | Detected and rejected as a bot within seconds. |
| 3 | Headless Chrome | `navigator.webdriver` gave us away. Cloudflare blocked us. |
| 4 | **Playwright Stealth** | Finally. It worked. |

The breakthrough came from understanding that modern anti-bot systems don't just check your user-agent string. They check browser fingerprints (plugins, screen resolution, hardware concurrency), behavioral patterns (scroll speed, mouse movements, timing), and dozens of other signals. We had to spoof *all of them* convincingly.

```python
# Every anti-bot check gets spoofed at the browser level
await context.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
""")
```

The result: we reliably crawl **DevPost, DoraHacks, MLH, TAIKAI, HackQuest, and Intigriti** — platforms that block most scrapers — using a fleet of stealth Playwright instances with randomized fingerprints and human-like browsing patterns.

Our **Sentinel** (proactive patrol worker) runs on a schedule, sweeping all major platforms in batched, staggered bursts to avoid rate-limiting. And our **Scout** (reactive worker) can be dispatched on-demand by the AI chat assistant when a student needs something specific — generating Google dork queries and crawling targeted results in real-time.

---

### The Brain: Cortex AI Pipeline

Raw HTML is useless on its own. The real magic is turning a wall of messy, inconsistent web content into structured, actionable opportunity data. Our pipeline has three stages:

**Stage 1 — The ReaderLLM (Gemini 2.0 Flash)**

When raw HTML arrives, **Gemini 2.0 Flash** acts as our extraction engine. It doesn't just parse tags — it *reads* the page like a human would, pulling out:
- Title, organization, description
- Exact deadlines and prize amounts
- Eligibility requirements (GPA, citizenship, background)
- Geographic scope and participation mode
- Application URLs and platform source

The model can handle both single opportunity pages *and* list/aggregator pages (like DevPost's hackathon listings), extracting up to 50 opportunities from a single page load. We enforce structured JSON output with strict validation.

**Stage 2 — The CortexFlinkProcessor (Stream Processing)**

Every extracted opportunity passes through our Python-native stream processor — inspired by Apache Flink's windowed processing model, but built to run entirely in-process without external infrastructure dependencies.

| Capability | How It Works |
|---|---|
| **Deduplication** | Content-based fingerprinting (URL + normalized title + org) with Firestore-persisted state across restarts |
| **Classification** | Auto-tags opportunities as Hackathon, Bounty, Scholarship, or Grant based on content analysis |
| **Expiration** | Purges opportunities with elapsed deadlines |
| **Platform Detection** | Routes to platform-specific parsing profiles |

This processor maintains a sliding window with in-memory dedup sets *and* Firestore persistence, so even after a cold restart, we never show duplicate results.

**Stage 3 — Vectorization & Matching**

Every surviving opportunity gets vectorized by `embedding-001` and stored with its semantic embedding. When you open your dashboard, the **Matching Engine** runs our **70/30 Formula**:

```
Match Score = (Cosine Similarity × 0.70) + (Heuristic Filters × 0.30)
```

The vector component captures *semantic* fit — "your story matches this opportunity's purpose." The heuristic component handles hard filters — location eligibility, GPA thresholds, skill keyword overlap. Together, they produce a match score that's smarter than either approach alone.

---

### The Nervous System: Event-Driven Architecture

ScholarStream uses an in-process **event broker** built on `asyncio.Queue` with topic-based pub/sub routing. This is the backbone that connects every component:

```
Crawler discovers opportunity
    → publishes to "cortex.raw.html.v1"
        → ReaderLLM subscribes, extracts structured JSON
            → publishes to "opportunity.enriched.v1"
                → CortexFlinkProcessor deduplicates & classifies
                    → Matching Engine scores against user profiles
                        → WebSocket pushes to dashboard — live
```

This architecture gives us Kafka-like decoupling and event-driven flow without external infrastructure costs. Every component is a subscriber that reacts to events, making the system testable, extensible, and resilient.

---

### The Delivery: Real-Time WebSocket

A FastAPI backend consumes the enriched stream, calculates personalized match scores against each user's Digital DNA vector, and pushes new opportunities directly to the React dashboard via WebSocket connections.

**No polling. No refreshing.** You're looking at your dashboard, and a new $10,000 hackathon that matches your skills just... appears. That's what real-time feels like for the student who needs it.

---

### The Fortress: Docker & Google Cloud Run

ScholarStream is fully containerized and deployed to **Google Cloud Run** for elastic, serverless scaling:

- **Dockerized backend** with hardened containers that include Playwright's browser dependencies for headless crawling at scale
- **Dockerized React frontend** served via Nginx, optimized for global CDN delivery
- **Cloud Run auto-scaling** — scales to zero when idle (saving costs), bursts to handle traffic spikes during major hackathon deadlines or tuition cycles
- **Firebase/Firestore** for user profiles, opportunity persistence, application tracking, and chat history
- **Upstash Redis** for real-time mission tracking with circuit-breaker fault tolerance
- **Automated deployment** via scripts that synchronize environment secrets and orchestrate build cycles

---

## The "Emergency Room": AI Chat Assistant

Sometimes a dashboard isn't enough. When a student is in financial crisis, they don't need a search bar — they need someone who *gets it*.

Our AI Chat Assistant is far more than a chatbot. It's a **true ReAct agent** powered by Gemini with function calling — meaning it reasons about your situation, decides what tools to use, executes actions, observes results, and then responds with genuine understanding.

### How The Agent Thinks

When you say *"I need $500 by Friday for textbooks,"* the agent doesn't just grep a database. It runs a reasoning loop:

1. **Reason**: "This is an urgent, small-dollar need. I should search for quick-turnaround bounties and emergency grants first."
2. **Act**: Calls `vector_search` with your query embedding to find semantically relevant opportunities
3. **Observe**: "Found 3 bounties and 1 emergency fund, but nothing in the student's exact skill area."
4. **Act**: Calls `dispatch_scout` to send live Playwright crawlers searching the web specifically for React bounties
5. **Observe**: "Scout found 2 more opportunities from Gitcoin and HackerOne."
6. **Respond**: Synthesizes everything into an empathetic, actionable response with prioritized next steps.

### The Five Tools

| Tool | What It Does |
|---|---|
| `search_database` | Filtered search across local opportunity database |
| `vector_search` | Semantic similarity search using cosine distance between query and opportunity embeddings |
| `dispatch_scout` | Sends live Playwright stealth crawlers to hunt the web for specific needs |
| `get_user_info` | Retrieves the student's profile for context-aware recommendations |
| `filter_opportunities` | Applies demographic and eligibility filters to results |

The agent decides autonomously which tools to call — and in what order — based on the student's message. This isn't a scripted chatbot. It's an AI that thinks, acts, and adapts.

---

## The Game-Changer: AI Co-Pilot Chrome Extension

Finding the right opportunity is half the battle. **Winning it** — that's what actually changes a student's life. And that's what the Chrome Extension does.

### What Makes It Different

Most hackathon projects stop at "we show you data." ScholarStream goes further. We built a **Chrome Extension (Manifest V3)** that acts as your personal, context-aware application assistant — and it works on the actual platforms where you apply.

### How It Works

1. **Navigate** to any application page — DevPost, DoraHacks, MLH, Kaggle, HackerOne
2. The extension **scans the page**: detects form fields, character limits, required flags, platform-specific nuances
3. **Focus on any text field** → A pulsing ✨ Sparkle button appears
4. **Click once** → AI generates personalized content using the **Tri-Fold Knowledge Base**
5. Content **streams with typewriter effect** — respecting exact character limits

### The Tri-Fold Knowledge Base

This is the core innovation. The AI doesn't generate generic responses. It draws from three knowledge sources simultaneously:

```
┌─────────────────────────────────────────────────────────────┐
│                    TRI-FOLD KNOWLEDGE BASE                   │
├───────────────────┬────────────────────┬────────────────────┤
│   YOUR PROFILE    │   YOUR DOCUMENTS   │   FIELD CONTEXT    │
│   ─────────────   │   ──────────────   │   ─────────────    │
│   • Skills        │   • @resume        │   • Character limit │
│   • Background    │   • @readme        │   • Platform tips   │
│   • GPA           │   • @cover_letter  │   • Required format │
│   • Experience    │   • @transcript    │   • Question intent │
└───────────────────┴────────────────────┴────────────────────┘
```

You can upload multiple documents (PDFs, resumes, project READMEs) and use **@mentions** in your prompt to tell the Co-Pilot exactly which knowledge base to draw from. *"Use @resume for this answer"* or *"Reference @readme and focus on the technical implementation."*

### Double-Click Refinement

Not happy with the generated text? **Double-click** it. A prompt appears right there in the form field. Tell the AI: *"Make it more professional"* or *"Focus on my leadership experience."* It rewrites in place. You never leave the form.

### Platform-Specific Intelligence

The extension carries specialized personas for each platform:

| Platform | What The AI Knows |
|---|---|
| **DevPost** | Hackathon project showcase best practices, team descriptions, "How it works" framing |
| **DoraHacks** | BUIDL format, bounty-specific language, Web3 ecosystem conventions |
| **MLH** | Student hackathon norms, beginner-friendly tone, community emphasis |
| **Kaggle** | Data science methodology, notebook structure, evaluation metrics |
| **HackerOne** | Vulnerability reporting format, severity classification, reproduction steps |

### Unified Authentication

The Chrome Extension runs in an isolated browser context — it can't share cookies or localStorage with the web app. We solved this with event-based auth sync:

```javascript
// Web app dispatches auth event on login
window.dispatchEvent(new CustomEvent('scholarstream-auth-sync', {
    detail: { token: firebaseToken, user: firebaseUser }
}));

// Extension content script listens and stores in chrome.storage
window.addEventListener('scholarstream-auth-sync', (event) => {
    chrome.storage.local.set({
        authToken: event.detail.token,
        user: event.detail.user
    });
});
```

Log in once on ScholarStream. The extension inherits your session automatically. Zero friction.

---

## Challenges I Ran Into

### 1. The Anti-Bot Wall

Every platform we needed to crawl — DevPost, DoraHacks, MLH, SuperTeam — actively blocks scrapers. We went through four complete iterations before Playwright Stealth worked. The learning curve was steep, and it took weeks of debugging browser fingerprint leaks, Cloudflare challenge pages, and rate-limiting patterns to get reliable results (I almost missed the hackathon deadline, thanks for extending it by a week).

### 2. AI Hallucination on Messy HTML

Gemini doesn't "just work" on raw web content. Early on, the model would hallucinate deadlines, invent prize amounts, or merge two different opportunities into one. We had to build extensive prompt engineering with strict JSON output schemas, field-level validation, and graceful degradation — treating the AI like any unreliable API with retries, format enforcement, and sanity checks.

### 3. Developing From Nigeria

Building from Nigeria means dealing with 400ms+ latency to cloud services, frequent power outages, and unstable internet. I had to architect every network-dependent operation for resilience — aggressive timeouts, retry logic with exponential backoff, and offline-safe local processing so that a 30-second internet dropout didn't corrupt state or lose data.

### 4. Cross-Context Chrome Extension Auth

The Chrome Extension runs in a completely isolated execution context. No shared cookies, no shared localStorage. It took real engineering to build the event-based auth sync bridge that makes the extension feel seamless — you log in once and everything just works. This also meant solving Manifest V3 constraints around service worker lifecycle management and content script injection timing.

---

## Accomplishments I'm Proud Of

| What We Built | Why It Matters |
|---|---|
| **ReAct AI Agent** | Not a scripted chatbot — a genuine reasoning agent that decides what tools to use based on context |
| **Tri-Fold Co-Pilot** | The extension doesn't just fill forms — it understands the platform, the question, and *you* |
| **Stealth Crawler Fleet** | Successfully crawls 6+ major platforms that block standard bots |
| **768-Dimensional Matching** | Semantic embedding-based matching that finds connections keyword search misses |
| **70/30 Match Formula** | Hybrid vector + heuristic scoring that's smarter than either approach alone |
| **Event-Driven Pipeline** | From crawl to dashboard in seconds, with deduplication and auto-expiration |
| **Zero-Friction Auth Sync** | One login. Web app and extension in perfect sync. |

---

## What I Learned

### AI Is a Tool, Not Magic
Gemini is incredibly powerful, but it needs structured prompts, output format specs, error handling for hallucinations, and rate limiting with graceful fallbacks. We treat AI like any API: validate inputs, verify outputs, retry on failure. The students relying on this can't afford a hallucinated deadline.

### The Best Architecture Is the Simplest One That Works
I could have added a dozen more moving parts. Instead, I chose an in-process event broker over distributed message queues, Firestore over a separate vector database, and Python-native stream processing over external compute engines. Fewer dependencies. Fewer failure points. Faster iteration. The architecture serves the mission, not the other way around.

### Real-World Problems Don't Fit Neatly Into Tutorials
Anti-bot detection, Chrome Extension auth isolation, AI output validation, high-latency network resilience from Nigeria — none of these had clean Stack Overflow answers. Each one required deep investigation, multiple failed approaches, and eventual breakthrough. That's the real work.

---

## What's Next

| Priority | Feature |
|---|---|
| 📱 **Immediate** | Flutter mobile app with push notifications for deadline alerts |
| 📋 **Near-term** | Application lifecycle tracking: Draft → Submitted → Under Review → Awarded |
| 👥 **Long-term** | Community features — success stories, team formation, peer mentorship |
| 🌍 **Vision** | Expand beyond tech — scholarships for nursing students, art programs, trade schools |

---

## The Vision

This project is deeply personal. Every line of code carries the weight of sitting at home since March 2025, watching my classmates move on without me. Every feature is designed for the student refreshing their bank account at 2 AM, wondering how they'll pay tuition tomorrow.

**ScholarStream exists so that no student ever has to say:**

> *"I had to defer my education because I didn't know."*

**Now they'll know. Now they'll find. Now they'll win.**

---

## Built With

<table>
  <tr>
    <td valign="top">
      <strong>Google Cloud AI</strong>
      <ul>
        <li>Gemini 2.0 Flash (LLM extraction & reasoning)</li>
        <li>embedding-001 (768-dim semantic vectors)</li>
        <li>Vertex AI SDK</li>
        <li>Cloud Run (serverless deployment)</li>
        <li>Firebase / Firestore</li>
      </ul>
    </td>

    <td valign="top">
      <strong>Backend Stack</strong>
      <ul>
        <li>Python / FastAPI</li>
        <li>Playwright Stealth (crawler fleet)</li>
        <li>Asyncio Event-Driven Broker</li>
        <li>BeautifulSoup / httpx</li>
        <li>Upstash Redis (mission tracking)</li>
        <li>WebSocket (real-time delivery)</li>
      </ul>
    </td>

    <td valign="top">
      <strong>Frontend & Extension</strong>
      <ul>
        <li>React / TypeScript</li>
        <li>Chrome Extension (Manifest V3)</li>
        <li>Vite (build tooling)</li>
        <li>Firebase Auth</li>
        <li>Docker / Nginx</li>
      </ul>
    </td>
  </tr>
</table>

---

<p align="center">
  <strong><em>The opportunities exist. Now you'll find them.</em></strong>
</p>