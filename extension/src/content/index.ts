console.log("ScholarStream Content Script Loaded");

import { getPageContext } from '../utils/domScanner';

// API Configuration - matches extension config
// API Configuration - Hardcoded for production
const API_URL = 'https://scholarstream-backend-opdnpd6bsq-uc.a.run.app';
/*
const API_URL = '__VITE_API_URL__' !== '__VITE_API_URL__'
    ? '__VITE_API_URL__'
    : 'http://localhost:8081';
*/

const ENDPOINTS = {
    mapFields: `${API_URL}/api/extension/map-fields`,
};

// ========== ENHANCED FIELD CONTEXT (Phase 3) ==========
interface FieldContext {
    // Basic
    id: string;
    name: string;
    label: string;
    placeholder: string;
    type: string;
    selector: string;

    // Enhanced (Phase 3)
    characterLimit?: number;
    wordLimit?: number;
    format: 'plain' | 'markdown' | 'html';
    isRequired: boolean;
    surroundingContext: string;
    platformHint: string;
    fieldCategory: FieldCategory;

    // Page context
    pageTitle: string;
    pageUrl: string;
}

type FieldCategory =
    | 'elevator_pitch'
    | 'description'
    | 'inspiration'
    | 'technical'
    | 'challenges'
    | 'team'
    | 'personal_info'
    | 'links'
    | 'generic';

// Platform-specific tips for thought bubble
const PLATFORM_TIPS: Record<string, string[]> = {
    DevPost: [
        "DevPost judges love clear problem statements",
        "Mention specific technologies and APIs used",
        "Highlight what makes your solution unique",
        "Include demo links or video if available"
    ],
    DoraHacks: [
        "Emphasize blockchain/Web3 aspects if relevant",
        "Highlight technical innovation",
        "Mention open-source contributions",
        "Show traction or community interest"
    ],
    MLH: [
        "Focus on what you learned during the hackathon",
        "Highlight team collaboration",
        "Mention any sponsors' technologies you used",
        "Be enthusiastic and authentic"
    ],
    Default: [
        "Be specific and avoid generic statements",
        "Use concrete examples and numbers",
        "Keep it concise but impactful",
        "Proofread for clarity"
    ]
};

// ===== UNIFIED AUTH SYNC: Listen for custom events from ScholarStream web app =====
// This is the Google-style zero-config approach (no extension ID needed)
window.addEventListener('scholarstream-auth-sync', ((event: CustomEvent) => {
    const { token, user } = event.detail || {};
    if (!token) return;

    console.log('🔑 [EXT] Auth sync event received from web app!');

    chrome.storage.local.set({
        authToken: token,
        userProfile: user || {}
    }, () => {
        console.log('✅ [EXT] Auth synced to extension storage');
    });
}) as EventListener);

window.addEventListener('scholarstream-auth-logout', () => {
    console.log('🚪 [EXT] Logout event received');
    chrome.storage.local.remove(['authToken', 'userProfile', 'lastLoggedToken']);
});

// ===== FALLBACK: Also poll localStorage for auth token (for pages already loaded) =====
if (window.location.host.includes('localhost') || window.location.host.includes('scholarstream')) {
    const extractAndSendToken = () => {
        let token = localStorage.getItem('scholarstream_auth_token');

        if (!token) {
            Object.keys(localStorage).forEach(key => {
                if (key.includes('firebase:authUser')) {
                    try {
                        const user = JSON.parse(localStorage.getItem(key) || '{}');
                        if (user.stsTokenManager && user.stsTokenManager.accessToken) {
                            token = user.stsTokenManager.accessToken;
                        }
                    } catch (e) {
                        // ignore parse errors
                    }
                }
            });
        }

        if (token) {
            chrome.storage.local.get(['authToken'], (result) => {
                // Only update if different (avoid unnecessary writes)
                if (result.authToken !== token) {
                    chrome.storage.local.set({ authToken: token }, () => {
                        console.log('🔑 [EXT] Firebase token captured via localStorage poll');
                    });
                }
            });
        }
    };

    // Initial check + periodic poll (less aggressive)
    extractAndSendToken();
    setInterval(extractAndSendToken, 5000);
}

// ===== INTELLIGENT SPARKLE ENGINE (Phase 3) =====
class FocusEngine {
    private activeElement: HTMLElement | null = null;
    private sparkleBtn: HTMLDivElement;
    private tooltip: HTMLDivElement;
    private thoughtBubble: HTMLDivElement;
    private guidanceBubble: HTMLDivElement;
    private refinementOverlay: HTMLDivElement; // NEW: In-field refinement
    private isStreaming = false;
    private isDragging = false;
    private dragOffset = { x: 0, y: 0 };
    private sparkleHidden = false;
    private lastFilledElement: HTMLElement | null = null; // Track last filled element

    constructor() {
        this.sparkleBtn = this.createSparkleButton();
        this.tooltip = this.createTooltip();
        this.thoughtBubble = this.createThoughtBubble();
        this.guidanceBubble = this.createGuidanceBubble();
        this.refinementOverlay = this.createRefinementOverlay(); // NEW
        this.initListeners();
    }

    private createSparkleButton(): HTMLDivElement {
        const container = document.createElement('div');
        container.id = 'ss-sparkle-container';
        container.style.cssText = `
            position: absolute;
            display: none;
            z-index: 2147483647;
            cursor: grab;
        `;

        const btn = document.createElement('div');
        btn.id = 'ss-sparkle-trigger';
        btn.style.cssText = `
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #FF6B6B, #4ECDC4);
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
            animation: ss-pulse 2s infinite;
        `;
        btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"></path></svg>`;

        const closeBtn = document.createElement('div');
        closeBtn.id = 'ss-sparkle-close';
        closeBtn.style.cssText = `
            position: absolute;
            top: -8px;
            right: -8px;
            width: 18px;
            height: 18px;
            background: #ef4444;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            opacity: 0;
            transition: opacity 0.2s;
        `;
        closeBtn.innerHTML = '×';

        container.appendChild(btn);
        container.appendChild(closeBtn);

        container.onmouseenter = () => {
            closeBtn.style.opacity = '1';
            if (!this.isDragging) btn.style.transform = 'scale(1.1)';
        };
        container.onmouseleave = () => {
            closeBtn.style.opacity = '0';
            btn.style.transform = 'scale(1)';
        };

        const style = document.createElement('style');
        style.textContent = `
            @keyframes ss-pulse { 0% { box-shadow: 0 0 0 0 rgba(78, 205, 196, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(78, 205, 196, 0); } 100% { box-shadow: 0 0 0 0 rgba(78, 205, 196, 0); } }
            @keyframes ss-typewriter { from { width: 0; } to { width: 100%; } }
            @keyframes ss-fade-in-up { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
            #ss-sparkle-container.dragging { cursor: grabbing !important; }
            @keyframes ss-bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
            @keyframes ss-spin { to { transform: rotate(360deg); } }
        `;
        document.head.appendChild(style);
        document.body.appendChild(container);

        btn.onclick = (e) => {
            if (this.isDragging) return;
            e.preventDefault();
            e.stopPropagation();
            this.handleSparkleClick();
        };

        closeBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.sparkleHidden = true;
            this.hideSparkle();
        };

        container.onmousedown = (e) => {
            if ((e.target as HTMLElement).id === 'ss-sparkle-close') return;
            this.isDragging = true;
            container.classList.add('dragging');
            const rect = container.getBoundingClientRect();
            this.dragOffset = {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };
        };

        document.addEventListener('mousemove', (e) => {
            if (!this.isDragging) return;
            container.style.left = `${e.clientX - this.dragOffset.x + window.scrollX}px`;
            container.style.top = `${e.clientY - this.dragOffset.y + window.scrollY}px`;
        });

        document.addEventListener('mouseup', () => {
            if (this.isDragging) {
                this.isDragging = false;
                container.classList.remove('dragging');
            }
        });

        return container as HTMLDivElement;
    }

    private createTooltip() {
        const div = document.createElement('div');
        div.style.cssText = `
            position: absolute;
            display: none;
            background: #1e293b;
            color: #fff;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            font-family: sans-serif;
            z-index: 2147483647;
            pointer-events: none;
            white-space: nowrap;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        `;
        div.innerText = "✨ Auto-Fill with ScholarStream";
        document.body.appendChild(div);
        return div;
    }

    private createThoughtBubble() {
        const div = document.createElement('div');
        div.id = 'ss-thought-bubble';
        div.style.cssText = `
            position: absolute;
            display: none;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            color: #e2e8f0;
            padding: 14px 18px;
            border-radius: 12px;
            border: 1px solid #334155;
            font-size: 13px;
            font-family: 'Inter', system-ui, sans-serif;
            line-height: 1.5;
            max-width: 360px;
            z-index: 2147483647;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            pointer-events: none;
            opacity: 0;
            transform: translateY(10px);
            transition: opacity 0.3s, transform 0.3s;
        `;
        document.body.appendChild(div);
        return div;
    }

    private createGuidanceBubble() {
        const div = document.createElement('div');
        div.id = 'ss-guidance-bubble';
        div.style.cssText = `
            position: absolute;
            display: none;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            color: #e2e8f0;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid #3b82f6;
            font-size: 13px;
            font-family: 'Inter', system-ui, sans-serif;
            line-height: 1.5;
            max-width: 320px;
            z-index: 2147483647;
            box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.3);
            opacity: 0;
            transform: translateY(10px);
            transition: opacity 0.3s, transform 0.3s;
        `;
        document.body.appendChild(div);
        return div;
    }

    // NEW: Create Refinement Overlay (Double-click to refine)
    private createRefinementOverlay(): HTMLDivElement {
        const overlay = document.createElement('div');
        overlay.id = 'ss-refinement-overlay';
        overlay.style.cssText = `
            position: absolute;
            display: none;
            z-index: 2147483647;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 2px solid #3b82f6;
            border-radius: 12px;
            padding: 12px;
            box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.5);
            min-width: 320px;
            max-width: 420px;
        `;
        overlay.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                <div style="width: 24px; height: 24px; background: linear-gradient(135deg, #FF6B6B, #4ECDC4); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"></path></svg>
                </div>
                <span style="font-size: 13px; font-weight: 600; color: #e2e8f0; font-family: system-ui, sans-serif;">Refine Content</span>
                <button id="ss-refinement-close" style="margin-left: auto; background: none; border: none; color: #64748b; cursor: pointer; font-size: 18px; padding: 0;">×</button>
            </div>
            <textarea 
                id="ss-refinement-input" 
                placeholder="e.g., Make it more detailed, add my Python experience..."
                style="width: 100%; padding: 10px 12px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: #e2e8f0; font-size: 13px; font-family: system-ui, sans-serif; outline: none; box-sizing: border-box; min-height: 42px; max-height: 120px; resize: none; overflow-y: auto; line-height: 1.4;"
                rows="1"
            ></textarea>
            <div style="display: flex; gap: 8px; margin-top: 10px;">
                <button id="ss-refinement-expand" style="flex: 1; padding: 8px 12px; background: #1e293b; border: 1px solid #334155; border-radius: 6px; color: #94a3b8; font-size: 12px; cursor: pointer; font-family: system-ui, sans-serif;">📝 More detailed</button>
                <button id="ss-refinement-concise" style="flex: 1; padding: 8px 12px; background: #1e293b; border: 1px solid #334155; border-radius: 6px; color: #94a3b8; font-size: 12px; cursor: pointer; font-family: system-ui, sans-serif;">✂️ More concise</button>
                <button id="ss-refinement-submit" style="flex: 1; padding: 8px 12px; background: #3b82f6; border: none; border-radius: 6px; color: white; font-size: 12px; font-weight: 600; cursor: pointer; font-family: system-ui, sans-serif;">Refine ✨</button>
            </div>
        `;
        document.body.appendChild(overlay);

        // Event listeners for refinement
        overlay.querySelector('#ss-refinement-close')?.addEventListener('click', () => this.hideRefinementOverlay());
        overlay.querySelector('#ss-refinement-expand')?.addEventListener('click', () => this.applyQuickRefinement('Make this response more detailed and comprehensive. Add specific examples and elaborate on key points.'));
        overlay.querySelector('#ss-refinement-concise')?.addEventListener('click', () => this.applyQuickRefinement('Make this response more concise and to the point. Remove unnecessary words while keeping the core message.'));
        overlay.querySelector('#ss-refinement-submit')?.addEventListener('click', () => this.submitRefinement());

        // Auto-grow textarea
        const textarea = overlay.querySelector('#ss-refinement-input') as HTMLTextAreaElement;
        textarea?.addEventListener('input', (e) => {
            const target = e.target as HTMLTextAreaElement;
            target.style.height = 'auto';
            target.style.height = Math.min(target.scrollHeight, 120) + 'px';
        });
        textarea?.addEventListener('keydown', (e) => {
            if ((e as KeyboardEvent).key === 'Enter' && !(e as KeyboardEvent).shiftKey) {
                e.preventDefault();
                this.submitRefinement();
            }
            if ((e as KeyboardEvent).key === 'Escape') this.hideRefinementOverlay();
        });

        return overlay;
    }


    private initListeners() {
        document.addEventListener('focusin', (e) => this.handleFocus(e), true);
        document.addEventListener('scroll', () => this.updatePosition(), true);
        window.addEventListener('resize', () => this.updatePosition());

        // NEW: Double-click listener for refinement on filled fields
        document.addEventListener('dblclick', (e) => this.handleDoubleClick(e), true);
    }

    // NEW: Handle double-click for refinement
    private handleDoubleClick(e: MouseEvent) {
        const target = e.target as HTMLElement;
        if (!target) return;

        // Only trigger on input/textarea that has content
        if (!['INPUT', 'TEXTAREA'].includes(target.tagName)) return;

        const input = target as HTMLInputElement | HTMLTextAreaElement;
        if (input.type === 'file' || input.type === 'hidden' || input.type === 'submit') return;

        // Only show refinement if field has content (likely AI-filled)
        if (!input.value || input.value.trim().length < 20) return;

        // Prevent text selection on double-click
        e.preventDefault();

        this.lastFilledElement = input;
        this.showRefinementOverlay(input);
    }

    private showRefinementOverlay(target: HTMLElement) {
        const rect = target.getBoundingClientRect();
        const top = rect.bottom + window.scrollY + 8;
        const left = rect.left + window.scrollX;

        this.refinementOverlay.style.top = `${top}px`;
        this.refinementOverlay.style.left = `${left}px`;
        this.refinementOverlay.style.display = 'block';

        // Focus the input
        setTimeout(() => {
            (this.refinementOverlay.querySelector('#ss-refinement-input') as HTMLInputElement)?.focus();
        }, 100);
    }

    private hideRefinementOverlay() {
        this.refinementOverlay.style.display = 'none';
        (this.refinementOverlay.querySelector('#ss-refinement-input') as HTMLInputElement).value = '';
    }

    private async applyQuickRefinement(instruction: string) {
        (this.refinementOverlay.querySelector('#ss-refinement-input') as HTMLInputElement).value = instruction;
        await this.submitRefinement();
    }

    private async submitRefinement() {
        if (!this.lastFilledElement) return;

        const input = this.lastFilledElement as HTMLInputElement | HTMLTextAreaElement;
        const refinementInput = this.refinementOverlay.querySelector('#ss-refinement-input') as HTMLTextAreaElement;
        const instruction = refinementInput.value.trim();

        if (!instruction) {
            refinementInput.style.borderColor = '#ef4444';
            setTimeout(() => refinementInput.style.borderColor = '#334155', 1000);
            return;
        }

        const currentContent = input.value;
        const fieldContext = this.analyzeField(input);

        // Show loading state on button
        const submitBtn = this.refinementOverlay.querySelector('#ss-refinement-submit') as HTMLButtonElement;
        const originalText = submitBtn.innerText;
        submitBtn.innerText = 'Refining...';
        submitBtn.disabled = true;

        // FAANG UX: Hide overlay and show "Refining..." feedback on the INPUT FIELD ITSELF immediately
        this.hideRefinementOverlay();

        // Show refinement progress indicator on the field
        this.showEnhancedReasoning(
            `🔄 Refining: "${instruction.slice(0, 40)}..."`,
            input,
            fieldContext,
            false
        );

        try {
            const stored = await chrome.storage.local.get(['authToken', 'userProfile', 'documentStore']);
            const authToken = stored.authToken;
            if (!authToken) throw new Error('Not authenticated');

            // Get project context from document store
            let projectContext = '';
            if (stored.documentStore?.documents?.length > 0) {
                projectContext = stored.documentStore.documents
                    .map((d: any) => `--- ${d.filename} ---\n${d.content}`)
                    .join('\n\n');
            }

            const refinementPrompt = `TASK: Refine the following content based on user instruction.

CURRENT CONTENT:
${currentContent}

USER INSTRUCTION: ${instruction}

FIELD CONTEXT:
- Field Type: ${fieldContext.fieldCategory}
- Platform: ${fieldContext.platformHint}
${fieldContext.characterLimit ? `- Character Limit: ${fieldContext.characterLimit}` : ''}
${fieldContext.wordLimit ? `- Word Limit: ${fieldContext.wordLimit}` : ''}

IMPORTANT:
1. Maintain the core message and facts
2. Apply the user's refinement instruction
3. Keep the same approximate length unless instructed otherwise
4. Return ONLY the refined content, no explanations`;

            const response = await fetch(ENDPOINTS.mapFields, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    form_fields: [],
                    user_profile: stored.userProfile || {},
                    target_field: {
                        ...fieldContext,
                        existingContent: currentContent
                    },
                    project_context: projectContext,
                    instruction: refinementPrompt
                })
            });

            if (!response.ok) throw new Error('Refinement failed');

            const data = await response.json();
            const refinedContent = data.sparkle_result?.content || data.filled_value || currentContent;

            // Apply refined content with typewriter effect
            await this.typewriterEffect(input, refinedContent);

            // Show success feedback - replace the "Refining..." with success
            this.showEnhancedReasoning(
                `✅ Refined based on: "${instruction.slice(0, 50)}..."`,
                input,
                fieldContext,
                false
            );

        } catch (error) {
            console.error('Refinement failed:', error);
            // Show error on the field
            this.showEnhancedReasoning(
                `❌ Refinement failed. Try again.`,
                input,
                fieldContext,
                false
            );
        } finally {
            submitBtn.innerText = originalText;
            submitBtn.disabled = false;
        }
    }

    private handleFocus(e: FocusEvent) {
        const target = e.target as HTMLElement;
        if (!target) return;

        if (!['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) && !target.isContentEditable) {
            this.hideSparkle();
            return;
        }

        const input = target as HTMLInputElement;
        if (input.type === 'file' || input.type === 'hidden' || input.type === 'submit' || input.type === 'image') {
            this.hideSparkle();
            return;
        }

        this.activeElement = target;
        this.showSparkle(target);
    }

    private showSparkle(target: HTMLElement) {
        if (!target || this.sparkleHidden) return;
        const rect = target.getBoundingClientRect();

        const top = rect.top + window.scrollY + (rect.height / 2) - 16;
        const left = rect.right + window.scrollX - 40;

        this.sparkleBtn.style.top = `${top}px`;
        this.sparkleBtn.style.left = `${left}px`;
        this.sparkleBtn.style.display = 'flex';

        this.tooltip.style.top = `${top - 30}px`;
        this.tooltip.style.left = `${left - 60}px`;
    }

    private hideSparkle() {
        this.sparkleBtn.style.display = 'none';
        this.tooltip.style.display = 'none';
        this.thoughtBubble.style.opacity = '0';
        this.hideGuidanceBubble();
    }

    private updatePosition() {
        if (this.activeElement && this.sparkleBtn.style.display !== 'none') {
            this.showSparkle(this.activeElement);
        }
    }

    // ========== ENHANCED THOUGHT BUBBLE (Phase 3) ==========
    private showEnhancedReasoning(
        reasoning: string,
        target: HTMLElement,
        fieldContext: FieldContext,
        wasTemplateUsed: boolean
    ) {
        if (!target) return;

        const rect = target.getBoundingClientRect();
        const top = rect.bottom + window.scrollY + 8;
        const left = rect.left + window.scrollX;

        // Get platform-specific tips
        const platformTips = PLATFORM_TIPS[fieldContext.platformHint] || PLATFORM_TIPS.Default;
        const randomTip = platformTips[Math.floor(Math.random() * platformTips.length)];

        // Build thought bubble content
        let content = `<div style="margin-bottom: 8px;"><span style="color: #4ECDC4; font-weight: 600;">🧠 AI Thought:</span> ${reasoning}</div>`;

        // Add character/word limit info if applicable
        if (fieldContext.characterLimit) {
            content += `<div style="font-size: 11px; color: #94a3b8; margin-bottom: 6px;">📏 Character limit: ${fieldContext.characterLimit}</div>`;
        }
        if (fieldContext.wordLimit) {
            content += `<div style="font-size: 11px; color: #94a3b8; margin-bottom: 6px;">📝 Word limit: ~${fieldContext.wordLimit}</div>`;
        }

        // Add format hint
        if (fieldContext.format === 'markdown') {
            content += `<div style="font-size: 11px; color: #60a5fa; margin-bottom: 6px;">📑 Markdown formatting supported</div>`;
        }

        // Add platform tip
        content += `<div style="font-size: 11px; color: #fbbf24; margin-top: 8px; padding-top: 8px; border-top: 1px solid #334155;">💡 Tip: ${randomTip}</div>`;

        // Add template warning if used
        if (wasTemplateUsed) {
            content += `<div style="font-size: 11px; color: #f87171; margin-top: 6px;">⚠️ Template used - replace [BRACKETS] with your info</div>`;
        }

        this.thoughtBubble.innerHTML = content;
        this.thoughtBubble.style.top = `${top}px`;
        this.thoughtBubble.style.left = `${left}px`;
        this.thoughtBubble.style.maxWidth = `${Math.min(360, window.innerWidth - left - 20)}px`;
        this.thoughtBubble.style.display = 'block';

        void this.thoughtBubble.offsetWidth;

        this.thoughtBubble.style.opacity = '1';
        this.thoughtBubble.style.transform = 'translateY(0)';

        // Auto-hide after 12 seconds (longer for templates and refinements)
        const hideDelay = wasTemplateUsed ? 15000 : 12000;
        setTimeout(() => {
            this.thoughtBubble.style.opacity = '0';
            this.thoughtBubble.style.transform = 'translateY(10px)';
            setTimeout(() => {
                if (this.thoughtBubble.style.opacity === '0') {
                    this.thoughtBubble.style.display = 'none';
                }
            }, 300);
        }, hideDelay);
    }

    private showGuidanceBubble(target: HTMLElement, hasProfile: boolean, hasDocument: boolean, fieldType: string) {
        const rect = target.getBoundingClientRect();
        const top = rect.bottom + window.scrollY + 8;
        const left = rect.left + window.scrollX;

        let message = '';
        let buttons = '';

        if (!hasProfile && !hasDocument) {
            message = `
                <div style="margin-bottom: 8px; font-weight: 600; color: #fbbf24;">🤔 I can help, but I don't know much about you yet.</div>
                <div style="color: #94a3b8; margin-bottom: 12px;">
                    For a <strong>great ${fieldType}</strong>, I need:
                    <ul style="margin: 8px 0 0 16px; padding: 0;">
                        <li>Your project details (upload via sidebar)</li>
                        <li>Your background (complete your profile)</li>
                    </ul>
                </div>
            `;
            buttons = `
                <button id="ss-guidance-upload" style="flex: 1; background: #3b82f6; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;">Upload Doc</button>
                <button id="ss-guidance-profile" style="flex: 1; background: #1e293b; color: #94a3b8; border: 1px solid #334155; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;">Complete Profile</button>
                <button id="ss-guidance-try" style="flex: 1; background: #1e293b; color: #4ade80; border: 1px solid #22c55e; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;">Try Anyway</button>
            `;
        } else if (!hasDocument) {
            message = `
                <div style="margin-bottom: 8px; font-weight: 600; color: #60a5fa;">💡 I'll use your profile, but I don't have project context.</div>
                <div style="color: #94a3b8; margin-bottom: 12px;">
                    Upload a project README or description for better results on this ${fieldType} field.
                </div>
            `;
            buttons = `
                <button id="ss-guidance-upload" style="flex: 1; background: #3b82f6; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;">Upload Doc</button>
                <button id="ss-guidance-try" style="flex: 1; background: #22c55e; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;">Generate Anyway</button>
            `;
        }

        this.guidanceBubble.innerHTML = `
            ${message}
            <div style="display: flex; gap: 8px; margin-top: 8px;">
                ${buttons}
            </div>
        `;

        this.guidanceBubble.style.top = `${top}px`;
        this.guidanceBubble.style.left = `${left}px`;
        this.guidanceBubble.style.display = 'block';
        this.guidanceBubble.style.pointerEvents = 'auto';

        void this.guidanceBubble.offsetWidth;

        this.guidanceBubble.style.opacity = '1';
        this.guidanceBubble.style.transform = 'translateY(0)';

        setTimeout(() => {
            document.getElementById('ss-guidance-upload')?.addEventListener('click', () => {
                // Use safe sender to avoid unhandled promise rejections when the service worker is sleeping/reloading.
                void safeSendMessage({ type: 'OPEN_SIDE_PANEL' });
                this.hideGuidanceBubble();
            });
            document.getElementById('ss-guidance-profile')?.addEventListener('click', () => {
                window.open('https://scholarstream-frontend-opdnpd6bsq-uc.a.run.app/profile', '_blank');
                this.hideGuidanceBubble();
            });
            document.getElementById('ss-guidance-try')?.addEventListener('click', () => {
                this.hideGuidanceBubble();
                this.generateWithAvailableContext();
            });
        }, 100);
    }

    private hideGuidanceBubble() {
        this.guidanceBubble.style.opacity = '0';
        this.guidanceBubble.style.transform = 'translateY(10px)';
        setTimeout(() => {
            this.guidanceBubble.style.display = 'none';
        }, 300);
    }

    // ========== ENHANCED FIELD ANALYSIS (Phase 3) ==========
    private analyzeField(target: HTMLInputElement | HTMLTextAreaElement): FieldContext {
        const label = this.getLabel(target);
        const placeholder = target.placeholder || '';
        const combinedText = (label + ' ' + placeholder).toLowerCase();

        // Detect character/word limits
        const characterLimit = this.detectCharacterLimit(target);
        const wordLimit = this.detectWordLimit(target, label);

        // Detect format (markdown support)
        const format = this.detectFormat(target, combinedText);

        // Get surrounding context (nearby headings, descriptions)
        const surroundingContext = this.getSurroundingContext(target);

        // Detect platform
        const platformHint = this.detectPlatform();

        // Categorize field
        const fieldCategory = this.categorizeFieldEnhanced(label, placeholder, surroundingContext);

        return {
            id: target.id,
            name: target.name || '',
            label,
            placeholder,
            type: target.type || target.tagName.toLowerCase(),
            selector: uniqueSelector(target),
            characterLimit,
            wordLimit,
            format,
            isRequired: target.required || target.hasAttribute('aria-required'),
            surroundingContext,
            platformHint,
            fieldCategory,
            pageTitle: document.title,
            pageUrl: window.location.href,
        };
    }

    private detectCharacterLimit(target: HTMLInputElement | HTMLTextAreaElement): number | undefined {
        // Check maxlength attribute
        if (target.maxLength && target.maxLength > 0 && target.maxLength < 1000000) {
            return target.maxLength;
        }

        // Check for nearby character counter elements
        const parent = target.parentElement;
        if (parent) {
            const counterText = parent.innerText.match(/(\d+)\s*\/\s*(\d+)/);
            if (counterText) {
                return parseInt(counterText[2], 10);
            }
        }

        // Check data attributes
        const dataMax = target.getAttribute('data-max-length') || target.getAttribute('data-maxlength');
        if (dataMax) return parseInt(dataMax, 10);

        return undefined;
    }

    private detectWordLimit(target: HTMLElement, label: string): number | undefined {
        const combinedText = label.toLowerCase();

        // Common patterns: "300 words", "max 500 words", "word limit: 250"
        const wordMatch = combinedText.match(/(\d+)\s*words?/i);
        if (wordMatch) {
            return parseInt(wordMatch[1], 10);
        }

        // Check surrounding elements
        const parent = target.parentElement;
        if (parent) {
            const parentText = parent.innerText.toLowerCase();
            const parentMatch = parentText.match(/(\d+)\s*words?/i);
            if (parentMatch) {
                return parseInt(parentMatch[1], 10);
            }
        }

        return undefined;
    }

    private detectFormat(target: HTMLElement, combinedText: string): 'plain' | 'markdown' | 'html' {
        // Check for markdown indicators
        if (
            combinedText.includes('markdown') ||
            combinedText.includes('supports formatting') ||
            target.classList.contains('markdown') ||
            target.getAttribute('data-format') === 'markdown' ||
            // DevPost submission fields typically support markdown
            (window.location.hostname.includes('devpost') && target.tagName === 'TEXTAREA')
        ) {
            return 'markdown';
        }

        // Check for rich text editor indicators
        if (target.isContentEditable || target.classList.contains('richtext') || target.classList.contains('wysiwyg')) {
            return 'html';
        }

        return 'plain';
    }

    private getSurroundingContext(target: HTMLElement): string {
        const parts: string[] = [];

        // Get nearby heading
        let el: HTMLElement | null = target;
        for (let i = 0; i < 5 && el; i++) {
            el = el.parentElement;
            if (el) {
                const heading = el.querySelector('h1, h2, h3, h4, h5, h6');
                if (heading) {
                    parts.push(`Section: ${heading.textContent?.trim()}`);
                    break;
                }
            }
        }

        // Get helper text (common patterns)
        const parent = target.parentElement;
        if (parent) {
            const helper = parent.querySelector('.helper-text, .hint, .description, [class*="help"], small');
            if (helper && helper.textContent) {
                parts.push(`Hint: ${helper.textContent.trim().slice(0, 200)}`);
            }
        }

        // Get label's additional info
        const labelEl = document.querySelector(`label[for="${target.id}"]`);
        if (labelEl) {
            const small = labelEl.querySelector('small, span.optional, span.required');
            if (small && small.textContent) {
                parts.push(small.textContent.trim());
            }
        }

        return parts.join(' | ').slice(0, 500);
    }

    private detectPlatform(): string {
        const url = window.location.href.toLowerCase();
        if (url.includes('devpost.com')) return 'DevPost';
        if (url.includes('dorahacks.io')) return 'DoraHacks';
        if (url.includes('mlh.io')) return 'MLH';
        if (url.includes('taikai.network')) return 'Taikai';
        if (url.includes('gitcoin.co')) return 'Gitcoin';
        if (url.includes('immunefi.com')) return 'Immunefi';
        if (url.includes('hackerone.com')) return 'HackerOne';
        if (url.includes('intigriti.com')) return 'Intigriti';
        return 'Default';
    }

    private categorizeFieldEnhanced(label: string, placeholder: string, context: string): FieldCategory {
        const text = (label + ' ' + placeholder + ' ' + context).toLowerCase();

        if (text.includes('elevator') || text.includes('pitch') || text.includes('tagline')) return 'elevator_pitch';
        if (text.includes('description') || text.includes('about') || text.includes('overview')) return 'description';
        if (text.includes('inspiration') || text.includes('why') || text.includes('motivation') || text.includes('what inspired')) return 'inspiration';
        if (text.includes('built') || text.includes('how') || text.includes('technical') || text.includes('architecture') || text.includes('stack')) return 'technical';
        if (text.includes('challenge') || text.includes('obstacle') || text.includes('difficult') || text.includes('learned')) return 'challenges';
        if (text.includes('team') || text.includes('member') || text.includes('collaborat')) return 'team';
        if (text.includes('name') || text.includes('email') || text.includes('phone') || text.includes('linkedin') || text.includes('github')) return 'personal_info';
        if (text.includes('url') || text.includes('link') || text.includes('demo') || text.includes('video') || text.includes('repo')) return 'links';

        return 'generic';
    }

    private async handleSparkleClick() {
        if (!this.activeElement || this.isStreaming) return;

        const target = this.activeElement as HTMLInputElement;

        // CRITICAL FIX: Check for documents in NEW documentStore, not legacy projectContext
        const stored = await chrome.storage.local.get(['userProfile', 'documentStore']);
        const hasProfile = stored.userProfile && Object.keys(stored.userProfile).length > 0;

        // Check new multi-document store
        const documentStore = stored.documentStore as { documents: any[] } | undefined;
        const hasDocument = !!(documentStore?.documents && documentStore.documents.length > 0);

        console.log('[Sparkle] Context check:', {
            hasProfile,
            hasDocument,
            docCount: documentStore?.documents?.length || 0,
            docNames: documentStore?.documents?.map((d: any) => d.filename) || []
        });

        // Enhanced field analysis
        const fieldContext = this.analyzeField(target);

        // Show guidance if missing critical context for project-specific fields
        const needsProjectContext = ['elevator_pitch', 'description', 'inspiration', 'technical', 'challenges'].includes(fieldContext.fieldCategory);

        if (needsProjectContext && !hasDocument && !hasProfile) {
            this.showGuidanceBubble(target, hasProfile, hasDocument, fieldContext.fieldCategory.replace('_', ' '));
            return;
        }

        // Generate with available context
        await this.generateWithEnhancedContext(fieldContext, hasProfile, hasDocument);
    }

    private async generateWithEnhancedContext(fieldContext: FieldContext, hasProfile: boolean, hasDocument: boolean) {
        if (!this.activeElement) return;

        this.isStreaming = true;
        const target = this.activeElement as HTMLInputElement;

        // Animation: Spin
        const btn = this.sparkleBtn.querySelector('#ss-sparkle-trigger');
        if (btn) {
            btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" style="animation: ss-spin 1s linear infinite;"><circle cx="12" cy="12" r="10" opacity="0.25"/><path d="M12 2C6.48 2 2 6.48 2 12" opacity="0.75"/></svg>`;
        }

        try {
            const result = await generateFieldContentEnhanced(fieldContext, hasProfile, hasDocument);

            const content = result.sparkle_result?.content || result.filled_value || result.template_content;
            const reasoning = result.sparkle_result?.reasoning || result.reasoning || 'Generated based on available context';
            const wasTemplateUsed = !!result.template_content || (content && content.includes('['));

            if (content) {
                // Show enhanced reasoning with tips
                this.showEnhancedReasoning(reasoning, target, fieldContext, wasTemplateUsed);

                // Typewriter effect
                await this.typewriterEffect(target, content);
            }
        } catch (e) {
            console.error("Focus Fill Failed", e);
            // Show error feedback
            this.showEnhancedReasoning(
                "Failed to generate content. Try again or check your connection.",
                target,
                fieldContext,
                false
            );
        } finally {
            this.isStreaming = false;
            const btn = this.sparkleBtn.querySelector('#ss-sparkle-trigger');
            if (btn) {
                btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"></path></svg>`;
            }
        }
    }

    // Legacy method for backward compatibility
    private async generateWithAvailableContext() {
        if (!this.activeElement) return;
        const target = this.activeElement as HTMLInputElement;
        const fieldContext = this.analyzeField(target);

        // FIXED: Check documentStore instead of legacy projectContext
        const stored = await chrome.storage.local.get(['userProfile', 'documentStore']);
        const hasProfile = stored.userProfile && Object.keys(stored.userProfile).length > 0;
        const documentStore = stored.documentStore as { documents: any[] } | undefined;
        const hasDocument = !!(documentStore?.documents && documentStore.documents.length > 0);

        await this.generateWithEnhancedContext(fieldContext, hasProfile, hasDocument);
    }

    private getLabel(el: HTMLElement): string {
        return (
            document.querySelector(`label[for="${el.id}"]`)?.textContent?.trim() ||
            el.closest('label')?.textContent?.trim() ||
            el.previousElementSibling?.textContent?.trim() ||
            el.parentElement?.textContent?.trim() ||
            ''
        ).slice(0, 100);
    }

    private async typewriterEffect(element: HTMLInputElement | HTMLTextAreaElement, text: string) {
        element.value = "";
        element.focus();

        const speed = Math.max(10, Math.min(50, 1000 / text.length));

        for (let i = 0; i < text.length; i++) {
            element.value += text.charAt(i);
            element.dispatchEvent(new Event('input', { bubbles: true }));
            if (element.scrollTop !== undefined) element.scrollTop = element.scrollHeight;

            await new Promise(r => setTimeout(r, speed + Math.random() * 10));
        }
        element.dispatchEvent(new Event('change', { bubbles: true }));

        // FIXED: Use outline for success indicator instead of background (dark theme compatible)
        element.style.outline = "2px solid #22c55e";
        element.style.outlineOffset = "1px";
        setTimeout(() => {
            element.style.outline = "";
            element.style.outlineOffset = "";
        }, 2000);
    }
}

// Initialize Focus Engine
new FocusEngine();

// ========== ENHANCED API HELPER (Phase 3) ==========
async function generateFieldContentEnhanced(
    fieldContext: FieldContext,
    hasProfile: boolean,
    hasDocument: boolean
) {
    let userProfile: any = {};
    let projectContext = "";

    try {
        // CRITICAL FIX: Read last mentioned docs from chat session, NOT all documents
        // This ensures sparkle uses ONLY the docs that were @mentioned in the last chat message
        const stored = await chrome.storage.local.get([
            'userProfile',
            'documentStore',
            'kbSettings',
            'lastMentionedDocs',  // NEW: Docs mentioned in last chat
            'lastKbSettings'       // NEW: KB settings from last chat
        ]);

        userProfile = stored.userProfile || {};
        const documentStore = stored.documentStore as { documents: any[] } | undefined;
        const lastMentionedDocs = stored.lastMentionedDocs as { id: string; filename: string }[] | undefined;
        const lastKbSettings = stored.lastKbSettings as { includeProfile: boolean; hasMentionedDocs: boolean } | undefined;

        // STRICT KB SYNC: If docs were mentioned in chat, use ONLY those docs
        if (lastMentionedDocs && lastMentionedDocs.length > 0 && documentStore?.documents) {
            // Filter to only the mentioned documents
            const mentionedFilenames = new Set(lastMentionedDocs.map(d => d.filename.toLowerCase()));
            const mentionedDocs = documentStore.documents.filter((d: any) =>
                mentionedFilenames.has(d.filename.toLowerCase())
            );

            if (mentionedDocs.length > 0) {
                projectContext = mentionedDocs
                    .map((d: any) => `--- ${d.filename} ---\n${d.content}`)
                    .join('\n\n');
                console.log(`[Sparkle] Using ONLY ${mentionedDocs.length} mentioned doc(s):`,
                    mentionedDocs.map((d: any) => d.filename));
            }

            // Use the KB settings from the last chat (profile inclusion)
            if (lastKbSettings && !lastKbSettings.includeProfile) {
                console.log('[Sparkle] Profile excluded by last chat KB settings');
                userProfile = {};
            }
        } else if (documentStore?.documents && documentStore.documents.length > 0) {
            // NO docs were mentioned in chat - fallback: use all docs (backwards compatible)
            // But check kbSettings toggle
            const kbSettings = stored.kbSettings as { useProfileAsKnowledge?: boolean } | undefined;

            projectContext = documentStore.documents
                .map((d: any) => `--- ${d.filename} ---\n${d.content}`)
                .join('\n\n');
            console.log(`[Sparkle] No chat mentions - using all ${documentStore.documents.length} doc(s):`,
                documentStore.documents.map((d: any) => d.filename));

            // Apply KB toggle for profile
            if (kbSettings && kbSettings.useProfileAsKnowledge === false) {
                console.log('[Sparkle] Profile excluded by KB toggle');
                userProfile = {};
            }
        } else {
            console.log('[Sparkle] No documents available');
        }
    } catch (e) {
        console.error('[Sparkle] Failed to load context:', e);
    }

    const storedToken = (await chrome.storage.local.get(['authToken'])).authToken;
    if (!storedToken) {
        throw new Error('Not authenticated');
    }

    // Build enhanced instruction based on field analysis
    let instruction = `You are a professional application writer. TASK: Fill the "${fieldContext.fieldCategory.replace('_', ' ')}" field for this form.\n\n`;

    instruction += `CRITICAL INSTRUCTIONS:\n`;
    instruction += `1. You MUST use the information from the provided "User Profile" and "Project Context" (Blueprint).\n`;
    instruction += `2. Do NOT hallucinate details. If context is missing, use the profile to infer reasonable professional details.\n`;
    instruction += `3. Adapt your tone to be persuasive and professional.\n`;

    if (fieldContext.characterLimit) {
        instruction += `\nCONSTRAINT: STRICTLY limit your response to UNDER ${fieldContext.characterLimit} characters. This is a HARD limit.\n`;
    }
    if (fieldContext.wordLimit) {
        instruction += `\nCONSTRAINT: Aim for approximately ${fieldContext.wordLimit} words.\n`;
    }
    if (fieldContext.format === 'markdown') {
        instruction += `\nFORMAT: Use markdown formatting (bolding, lists) for readability.\n`;
    }
    if (fieldContext.surroundingContext) {
        instruction += `\nPAGE CONTEXT: ${fieldContext.surroundingContext}\n`;
    }

    // Request template if no context available
    if (!hasProfile && !hasDocument) {
        instruction += ` Since no profile or project context is available, generate a helpful template with [PLACEHOLDER] brackets that the user can fill in.`;
    } else if (!hasDocument && ['elevator_pitch', 'description', 'technical', 'challenges'].includes(fieldContext.fieldCategory)) {
        instruction += ` No project document uploaded - use profile info and generate helpful content with [PROJECT SPECIFIC DETAILS] placeholders where needed.`;
    }

    const response = await fetch(ENDPOINTS.mapFields, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${storedToken}`
        },
        body: JSON.stringify({
            form_fields: [],
            user_profile: userProfile,
            target_field: {
                ...fieldContext,
                // Flatten for backend compatibility
                id: fieldContext.id,
                name: fieldContext.name,
                type: fieldContext.type,
                placeholder: fieldContext.placeholder,
                label: fieldContext.label,
                characterLimit: fieldContext.characterLimit,
                wordLimit: fieldContext.wordLimit,
                format: fieldContext.format,
                fieldCategory: fieldContext.fieldCategory,
                platformHint: fieldContext.platformHint,
            },
            project_context: projectContext,
            instruction
        })
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    return await response.json();
}

// Legacy helper for backward compatibility
async function generateFieldContent(targetField: any) {
    let userProfile: any = {};
    try {
        const stored = await chrome.storage.local.get(['userProfile']);
        userProfile = stored.userProfile || {};
    } catch (e) { }

    const storedToken = (await chrome.storage.local.get(['authToken'])).authToken;
    if (!storedToken) {
        throw new Error('Not authenticated');
    }

    let projectContext = "";
    try {
        const stored = await chrome.storage.local.get(['projectContext']);
        projectContext = stored.projectContext || "";
    } catch (e) { }

    const response = await fetch(ENDPOINTS.mapFields, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${storedToken}`
        },
        body: JSON.stringify({
            form_fields: [],
            user_profile: userProfile,
            target_field: targetField,
            project_context: projectContext,
            instruction: "Fill this field based on my profile and project."
        })
    });

    return await response.json();
}

// Safe Message Sender
const safeSendMessage = async (message: any) => {
    if (!chrome.runtime?.id) {
        console.warn("Extension context invalidated. Reload page to reconnect.");
        return;
    }
    try {
        return await chrome.runtime.sendMessage(message);
    } catch (e) {
        const msg = (e as any).message || "";
        if (msg.includes("Extension context invalidated") || msg.includes("receiving end does not exist")) {
            console.log("Extension disconnected (reload needed).");
        } else {
            console.error("Message send failed:", e);
        }
    }
};

// Unique selector generator
function uniqueSelector(el: Element): string {
    if (el.id) return `#${el.id}`;
    if ((el as any).name) return `[name="${(el as any).name}"]`;
    return el.tagName.toLowerCase();
}

// Listen for context requests and Auto-Fill commands
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (!chrome.runtime?.id) return;

    try {
        if (message.type === 'GET_PAGE_CONTEXT') {
            const context = getPageContext();
            console.log("Creating context:", context.title);
            sendResponse(context);
        }

        if (message.type === 'AUTO_FILL_REQUEST') {
            console.log("Agentic Auto-Fill Triggered");
            handleAutoFill(message.projectContext).then(result => {
                try {
                    sendResponse(result);
                } catch (e) { /* Context likely lost during long op */ }
            });
            return true;
        }
    } catch (e) {
        console.error("Content Script Error:", e);
    }
});

async function handleAutoFill(projectContext?: string) {
    // ENHANCED: Better field detection - find ALL visible inputs including those in cards/sections
    const allInputs: HTMLElement[] = [];

    // Primary selector: All standard form elements
    document.querySelectorAll('input, select, textarea').forEach(el => allInputs.push(el as HTMLElement));

    // Also find contenteditable elements (rich text editors)
    document.querySelectorAll('[contenteditable="true"]').forEach(el => allInputs.push(el as HTMLElement));

    // Deduplicate by checking if element is already included
    const seenElements = new Set<HTMLElement>();
    const uniqueInputs = allInputs.filter(el => {
        if (seenElements.has(el)) return false;
        seenElements.add(el);
        return true;
    });

    const formFields = uniqueInputs.map((el: any) => {
        // Enhanced label detection - look in multiple places
        let label = '';

        // 1. Check for label[for="id"]
        if (el.id) {
            const labelEl = document.querySelector(`label[for="${el.id}"]`);
            if (labelEl) label = labelEl.textContent?.trim() || '';
        }

        // 2. Check if wrapped in label
        if (!label) {
            const closestLabel = el.closest('label');
            if (closestLabel) label = closestLabel.textContent?.trim() || '';
        }

        // 3. Check for previous sibling (often a label or heading)
        if (!label && el.previousElementSibling) {
            const prev = el.previousElementSibling;
            if (prev.tagName === 'LABEL' || prev.tagName.match(/^H[1-6]$/) || prev.classList.contains('label')) {
                label = prev.textContent?.trim() || '';
            }
        }

        // 4. Check parent for section heading or card title
        if (!label) {
            const parent = el.closest('section, .card, .form-group, [class*="field"], [class*="input"]');
            if (parent) {
                const heading = parent.querySelector('h1, h2, h3, h4, h5, h6, label, .label, [class*="title"], [class*="heading"]');
                if (heading && heading !== el) {
                    label = heading.textContent?.trim() || '';
                }
            }
        }

        // 5. Fallback: Check aria-label or data attributes
        if (!label) {
            label = el.getAttribute('aria-label') ||
                el.getAttribute('data-label') ||
                el.getAttribute('title') ||
                el.name?.replace(/[-_]/g, ' ') || '';
        }

        return {
            id: el.id || '',
            name: el.name || '',
            type: el.type || el.tagName.toLowerCase(),
            placeholder: el.placeholder || '',
            label: label.slice(0, 150), // Extended limit for more context
            selector: uniqueSelector(el),
            // Extra context for better matching
            ariaLabel: el.getAttribute('aria-label') || '',
            dataTestId: el.getAttribute('data-testid') || el.getAttribute('data-test') || '',
        };
    }).filter(f =>
        f.type !== 'hidden' &&
        f.type !== 'submit' &&
        f.type !== 'file' &&
        f.type !== 'button' &&
        f.type !== 'image' &&
        f.type !== 'reset'
    );

    if (formFields.length === 0) return { success: false, message: "No fields found" };

    console.log(`[Auto-Fill] Detected ${formFields.length} fields:`, formFields.map(f => f.label || f.name || f.id));

    let userProfile: any = {};
    try {
        const stored = await chrome.storage.local.get(['userProfile']);
        userProfile = stored.userProfile || {};
    } catch (e) {
        console.log("No stored profile, using empty");
    }

    try {
        const storedToken = (await chrome.storage.local.get(['authToken'])).authToken;
        if (!storedToken) {
            return { success: false, message: "Please sign in securely through the extension first." };
        }

        console.log(`🔑 [EXT] Using secure token for API call`);
        const response = await fetch(ENDPOINTS.mapFields, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${storedToken}`
            },
            body: JSON.stringify({
                form_fields: formFields,
                user_profile: userProfile,
                project_context: projectContext
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Backend error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        const fieldMappings = data.field_mappings || {};

        let filledCount = 0;
        for (const [selector, value] of Object.entries(fieldMappings)) {
            // CRITICAL FIX: Validate selector before using querySelector
            // The AI sometimes returns URLs or invalid strings as "selectors"
            if (!selector ||
                selector.startsWith('http') ||
                selector.startsWith('www.') ||
                selector.includes('://') ||
                (!selector.startsWith('#') && !selector.startsWith('.') && !selector.startsWith('[') && !selector.match(/^[a-zA-Z]/))) {
                console.warn(`[Auto-Fill] Invalid selector skipped: "${selector}"`);
                continue;
            }

            try {
                const el = document.querySelector(selector) as HTMLInputElement;
                if (el && value) {
                    if (el.type === 'file') continue;

                    el.value = String(value);
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    filledCount++;

                    // FIXED: Use outline instead of background to avoid readability issues on dark themes
                    el.style.outline = "2px solid #22c55e";
                    el.style.outlineOffset = "1px";
                    // Reset after 3 seconds
                    setTimeout(() => {
                        el.style.outline = "";
                        el.style.outlineOffset = "";
                    }, 3000);
                }
            } catch (selectorError) {
                console.warn(`[Auto-Fill] querySelector failed for "${selector}":`, selectorError);
            }
        }

        return { success: true, filled: filledCount };

    } catch (error) {
        console.error("Auto-Fill Failed:", error);
        return { success: false, error: String(error) };
    }
}

// ===== SIDE PANEL TRIGGER (PULSE ICON) =====
if (document.body.innerText.toLowerCase().includes('scholarship') ||
    document.body.innerText.toLowerCase().includes('hackathon') ||
    document.body.innerText.toLowerCase().includes('grant') ||
    window.location.hostname.includes('devpost') ||
    window.location.hostname.includes('dorahacks') ||
    window.location.hostname.includes('mlh') ||
    window.location.hostname.includes('taikai')) {

    const icon = document.createElement('div');
    icon.id = 'scholarstream-pulse-icon';
    icon.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      box-shadow: 0 4px 15px rgba(0,0,0,0.3);
      z-index: 9999;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.2s;
      background: transparent;
    `;

    const img = document.createElement('img');
    img.src = chrome.runtime.getURL("assets/ss_logo.png");
    img.style.width = "100%";
    img.style.height = "100%";
    img.style.objectFit = "cover";
    img.style.borderRadius = "50%";
    icon.appendChild(img);

    icon.onclick = () => {
        console.log("Pulse Clicked - Requesting Side Panel Open");
        safeSendMessage({ type: 'OPEN_SIDE_PANEL' });
    };

    document.body.appendChild(icon);
}
