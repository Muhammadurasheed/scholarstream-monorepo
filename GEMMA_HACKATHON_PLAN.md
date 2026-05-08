# ScholarStream: Gemma 4 Good Hackathon Execution Plan

**Project Vision**: To build the "Great Equalizer"—an AI-native discovery and application co-pilot that levels the playing field for students worldwide using Gemma 4.

---

## 🏗️ Phase 1: Foundation & Frictionless Compliance
*Target: 24 - 48 Hours*

### Objectives:
1. **No-Login Access**: Implement "Guest Mode" to satisfy Kaggle Rule #81.
2. **Infrastructure Pivot**: Migrate to the new GCP account with $300 credit.
3. **Public Presence**: Establish the storytelling repository.

### Key Tasks:
- [x] Create Public GitHub Repo (`scholarstream-gemma4good`).
- [x] Implement `GUEST_MODE` logic in Backend.
- [x] Create `populate_demo_guest.py` script for persona injection.
- [x] Add "Try Live Demo" button to Frontend/Extension.
- [x] Migrate Firestore/Cloud Run to new GCP project.

---

## 🧠 Phase 2: The Gemma 4 Integration (The Engine Swap)
*Target: Day 3 - 5*

### Objectives:
1. **Native Inference**: Replace Gemini API calls with native Gemma 4 inference.
2. **Agentic Reasoning**: Upgrade the ReAct agent to use Gemma 4 for decision-making.
3. **Multi-Platform Extraction**: Fine-tune prompts for Gemma 4 to handle DevPost/DoraHacks HTML.

### Key Tasks:
- [x] Deploy Gemma 4 Inference Server on Google Cloud (Vertex AI Maas).
- [x] Update `ChatService.py` to use the new Gemma endpoint.
- [x] Implement native ReAct loop for Gemma 4 (Reasoning Mode).
- [x] Verify "Sentinel" crawler performance with the new engine.

---

## ✨ Phase 3: The Sparkle V4 Engine (The "Wow" Factor)
*Target: Day 6 - 8*

### Objectives:
1. **Premium UX**: Implement the "Typewriter" effect for form auto-filling.
2. **Refinement Overlay**: Allow users to double-click fields to "Refine with AI" (Powered by Gemma).
3. **Contextual Knowledge**: Optimize the multi-doc RAG (Research Papers + Resume + Page Context).

### Key Tasks:
- [x] Implement Premium Typewriter effect with variable speed.
- [x] Integrate Typewriter effect into Bulk Autofill.
- [x] Add Glassmorphism "Refinement Overlay" to the extension.
- [x] Implement Evidence Engine for Achievement-based RAG (Deep Context).
- [ ] Benchmark "Gemma-powered" essay generation vs. Gemini.

---

## 🏆 Phase 4: Submission & Verification (The Home Stretch)
*Target: Day 9 - 11*

### Objectives:
1. **Technical Proof**: Publish the Kaggle "Source of Truth" Notebook.
2. **Compelling Story**: Record a high-production 3-minute demo video.
3. **Writeup**: Complete the 1,500-word technical analysis.

### Key Tasks:
- [ ] Create Kaggle Notebook (Demonstrating Extraction & Matching).
- [ ] Record Screen Demo (Focusing on the "Musa" Persona).
- [ ] Write Kaggle Writeup (Focus on "Digital Equity" & "Technical Depth").
- [ ] Final Submission prior to May 19th Deadline.

---

## ✅ Completion Checklist
- [ ] App is accessible without login/signup.
- [ ] Video is < 3 minutes and shows a "Real Story."
- [ ] Code Repo is Public and has a "Storytelling" history.
- [ ] Kaggle Notebook demonstrates Gemma 4 logic clearly.
- [ ] Writeup explains exactly HOW Gemma 4 was used.

Allahu Musta'an. Let's make history.
