/**
 * ScholarStream Copilot - Content Script
 * AI-powered auto-fill and essay assistant for scholarship/hackathon applications
 */

class ScholarStreamCopilot {
  constructor() {
    this.userProfile = null;
    this.currentOpportunity = null;
    this.fields = {};
    this.isEssayModalOpen = false;
    this.init();
  }

  async init() {
    this.userProfile = await this.getUserProfile();
    
    if (this.isApplicationPage()) {
      this.injectStyles();
      this.injectCopilotUI();
      this.detectFields();
      this.detectOpportunityContext();
    }
    
    // Listen for messages from background script
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      this.handleMessage(request).then(sendResponse);
      return true;
    });
  }

  handleMessage(request) {
    switch (request.action) {
      case 'autofill':
        return this.autoFillForm();
      case 'showImprovedText':
        return this.showImprovedTextModal(request.original, request.improved);
      case 'showResearch':
        return this.showResearchPanel(request.topic, request.research);
      default:
        return Promise.resolve({ success: false });
    }
  }

  isApplicationPage() {
    const url = window.location.href.toLowerCase();
    const urlKeywords = ['apply', 'application', 'submit', 'register', 'signup', 'form', 'scholarship', 'hackathon', 'bounty'];
    
    if (urlKeywords.some(kw => url.includes(kw))) return true;
    
    const forms = document.querySelectorAll('form');
    if (forms.length > 0) {
      const hasNameField = document.querySelector('input[name*="name"], input[id*="name"], input[placeholder*="name" i]');
      const hasEmailField = document.querySelector('input[type="email"]');
      const hasEssayField = document.querySelector('textarea[minlength], textarea[maxlength], textarea[rows]');
      return hasNameField && (hasEmailField || hasEssayField);
    }
    
    return false;
  }

  detectOpportunityContext() {
    this.currentOpportunity = {
      name: document.title.replace(/[-|].*/, '').trim(),
      url: window.location.href,
      organization: this.extractOrganization(),
      type: this.detectOpportunityType(),
      deadline: this.extractDeadline()
    };
  }

  detectOpportunityType() {
    const url = window.location.href.toLowerCase();
    const text = document.body.innerText.toLowerCase();
    
    if (url.includes('devpost') || url.includes('hackathon') || text.includes('hackathon')) return 'hackathon';
    if (url.includes('gitcoin') || url.includes('bounty') || text.includes('bounty')) return 'bounty';
    if (url.includes('kaggle') || text.includes('competition')) return 'competition';
    return 'scholarship';
  }

  extractDeadline() {
    const patterns = [
      /deadline[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})/i,
      /due[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})/i,
      /closes?[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4})/i,
      /(\d{1,2}\/\d{1,2}\/\d{2,4})/
    ];
    
    const text = document.body.innerText;
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) return match[1];
    }
    return null;
  }

  extractOrganization() {
    const domain = window.location.hostname.replace('www.', '');
    const parts = domain.split('.');
    return parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
  }

  injectStyles() {
    if (document.getElementById('scholarstream-styles')) return;
    
    const styles = document.createElement('style');
    styles.id = 'scholarstream-styles';
    styles.textContent = `
      /* ScholarStream Copilot Injected Styles */
      .ss-fade-in {
        animation: ssFadeIn 0.3s ease-out;
      }
      
      @keyframes ssFadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }
      
      .ss-typing {
        display: inline-flex;
        gap: 4px;
      }
      
      .ss-typing span {
        width: 6px;
        height: 6px;
        background: #6366f1;
        border-radius: 50%;
        animation: ssTyping 1.4s infinite;
      }
      
      .ss-typing span:nth-child(2) { animation-delay: 0.2s; }
      .ss-typing span:nth-child(3) { animation-delay: 0.4s; }
      
      @keyframes ssTyping {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-8px); }
      }
      
      .ss-highlight-field {
        outline: 2px solid #6366f1 !important;
        outline-offset: 2px;
        transition: outline 0.2s ease;
      }
    `;
    document.head.appendChild(styles);
  }

  injectCopilotUI() {
    if (document.getElementById('scholarstream-copilot-btn')) return;
    
    const copilotButton = document.createElement('div');
    copilotButton.id = 'scholarstream-copilot-btn';
    copilotButton.innerHTML = `
      <div class="copilot-fab">
        <div class="copilot-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <span class="copilot-label">ScholarStream</span>
      </div>
    `;
    
    copilotButton.addEventListener('click', () => this.toggleCopilotPanel());
    document.body.appendChild(copilotButton);
  }

  toggleCopilotPanel() {
    const existing = document.getElementById('scholarstream-copilot-panel');
    if (existing) {
      existing.remove();
      return;
    }
    this.showCopilotPanel();
  }

  showCopilotPanel() {
    const panel = document.createElement('div');
    panel.id = 'scholarstream-copilot-panel';
    panel.className = 'ss-fade-in';
    
    const profileStatus = this.userProfile 
      ? `<div class="profile-connected">
           <div class="profile-avatar">${this.userProfile.name?.[0]?.toUpperCase() || 'U'}</div>
           <div class="profile-info">
             <span class="profile-name">${this.userProfile.name || 'User'}</span>
             <span class="profile-school">${this.userProfile.school || 'Student'}</span>
           </div>
           <span class="status-badge connected">Synced</span>
         </div>`
      : `<div class="profile-disconnected">
           <span>⚠️ Profile not synced</span>
           <a href="https://scholarstream-v3.vercel.app/profile" target="_blank">Sync now</a>
         </div>`;
    
    const fieldCount = Object.values(this.fields).flat().length;
    const essayCount = this.fields.essay?.length || 0;
    
    panel.innerHTML = `
      <div class="copilot-panel">
        <div class="copilot-header">
          <div class="header-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2"/>
            </svg>
            <h3>ScholarStream Copilot</h3>
          </div>
          <button class="close-btn" id="ss-close-panel">×</button>
        </div>
        
        ${profileStatus}
        
        <div class="opportunity-context">
          <div class="context-badge ${this.currentOpportunity?.type || 'scholarship'}">
            ${this.getTypeIcon(this.currentOpportunity?.type)} ${this.currentOpportunity?.type || 'Application'}
          </div>
          <span class="opportunity-name">${this.currentOpportunity?.name || 'Application Form'}</span>
        </div>
        
        <div class="copilot-stats">
          <div class="stat">
            <span class="stat-number">${fieldCount}</span>
            <span class="stat-label">Fields Detected</span>
          </div>
          <div class="stat">
            <span class="stat-number">${essayCount}</span>
            <span class="stat-label">Essays Found</span>
          </div>
        </div>
        
        <div class="copilot-actions">
          <button class="btn-primary" id="ss-auto-fill">
            <span class="btn-icon">⚡</span>
            Auto-Fill Form
          </button>
          
          <button class="btn-secondary" id="ss-essay-help" ${essayCount === 0 ? 'disabled' : ''}>
            <span class="btn-icon">✍️</span>
            AI Essay Assistant
          </button>
          
          <button class="btn-secondary" id="ss-winning-tips">
            <span class="btn-icon">🏆</span>
            Winning Tips
          </button>
          
          <button class="btn-secondary" id="ss-track-app">
            <span class="btn-icon">📊</span>
            Track Application
          </button>
        </div>
        
        <div class="field-preview">
          <h4>Detected Fields</h4>
          <div class="field-chips" id="ss-field-chips"></div>
        </div>
        
        <div class="copilot-footer">
          <a href="https://scholarstream-v3.vercel.app/dashboard" target="_blank">Open Dashboard</a>
          <span>•</span>
          <a href="#" id="ss-refresh-fields">Refresh Detection</a>
        </div>
      </div>
    `;
    
    document.body.appendChild(panel);
    this.attachPanelListeners();
    this.displayFieldChips();
  }

  getTypeIcon(type) {
    const icons = {
      scholarship: '🎓',
      hackathon: '💻',
      bounty: '💰',
      competition: '🏅'
    };
    return icons[type] || '📝';
  }

  attachPanelListeners() {
    document.getElementById('ss-close-panel')?.addEventListener('click', () => {
      document.getElementById('scholarstream-copilot-panel')?.remove();
    });
    
    document.getElementById('ss-auto-fill')?.addEventListener('click', () => this.autoFillForm());
    document.getElementById('ss-essay-help')?.addEventListener('click', () => this.openEssayAssistant());
    document.getElementById('ss-winning-tips')?.addEventListener('click', () => this.showWinningTips());
    document.getElementById('ss-track-app')?.addEventListener('click', () => this.trackApplication());
    document.getElementById('ss-refresh-fields')?.addEventListener('click', (e) => {
      e.preventDefault();
      this.detectFields();
      this.displayFieldChips();
      this.showToast('Fields refreshed!', 'success');
    });
  }

  displayFieldChips() {
    const container = document.getElementById('ss-field-chips');
    if (!container) return;
    
    container.innerHTML = '';
    
    const categories = ['name', 'email', 'phone', 'school', 'gpa', 'major', 'essay'];
    categories.forEach(cat => {
      const count = this.fields[cat]?.length || 0;
      if (count > 0) {
        const chip = document.createElement('span');
        chip.className = `field-chip ${cat}`;
        chip.textContent = `${cat} (${count})`;
        chip.addEventListener('click', () => this.highlightFields(cat));
        container.appendChild(chip);
      }
    });
    
    if (container.children.length === 0) {
      container.innerHTML = '<span class="no-fields">No fields detected</span>';
    }
  }

  highlightFields(category) {
    // Remove existing highlights
    document.querySelectorAll('.ss-highlight-field').forEach(el => {
      el.classList.remove('ss-highlight-field');
    });
    
    // Highlight fields in category
    this.fields[category]?.forEach(field => {
      field.element.classList.add('ss-highlight-field');
      field.element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  }

  detectFields() {
    this.fields = {
      name: this.findFields(['name', 'full name', 'fullname', 'applicant', 'first name', 'last name']),
      email: this.findFields(['email', 'e-mail']),
      phone: this.findFields(['phone', 'telephone', 'mobile', 'cell']),
      address: this.findFields(['address', 'street', 'city', 'state', 'zip', 'postal']),
      school: this.findFields(['school', 'university', 'college', 'institution', 'education']),
      gpa: this.findFields(['gpa', 'grade point', 'grades', 'academic']),
      major: this.findFields(['major', 'field of study', 'concentration', 'degree', 'program']),
      essay: this.findEssayFields(),
      year: this.findFields(['year', 'graduation', 'class of', 'expected']),
      social: this.findFields(['linkedin', 'github', 'twitter', 'portfolio', 'website'])
    };
  }

  findFields(keywords) {
    const foundFields = [];
    const inputs = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]), select');
    
    inputs.forEach(input => {
      const searchText = this.getFieldSearchText(input);
      if (keywords.some(kw => searchText.includes(kw.toLowerCase()))) {
        foundFields.push({
          element: input,
          type: input.type || 'text',
          label: this.getFieldLabel(input),
          name: input.name || input.id
        });
      }
    });
    
    return foundFields;
  }

  findEssayFields() {
    const essayFields = [];
    const textareas = document.querySelectorAll('textarea');
    
    textareas.forEach(textarea => {
      const minLength = textarea.minLength || 0;
      const rows = textarea.rows || 1;
      const searchText = this.getFieldSearchText(textarea);
      
      // Essay-like if long or has essay-related labels
      const isEssay = minLength > 100 || rows > 3 || 
        ['essay', 'statement', 'describe', 'tell us', 'explain', 'why', 'how', 'what'].some(kw => searchText.includes(kw));
      
      if (isEssay) {
        essayFields.push({
          element: textarea,
          type: 'essay',
          label: this.getFieldLabel(textarea),
          name: textarea.name || textarea.id,
          prompt: this.extractEssayPrompt(textarea),
          maxLength: textarea.maxLength || null,
          minLength: minLength
        });
      }
    });
    
    return essayFields;
  }

  extractEssayPrompt(textarea) {
    // Look for prompt in nearby elements
    const parent = textarea.closest('.form-group, .field, .question, div');
    if (parent) {
      const promptEl = parent.querySelector('label, .label, .prompt, .question-text, h3, h4, p');
      if (promptEl) return promptEl.textContent.trim();
    }
    return this.getFieldLabel(textarea);
  }

  getFieldSearchText(element) {
    const label = this.getFieldLabel(element);
    const name = element.name || element.id || '';
    const placeholder = element.placeholder || '';
    const ariaLabel = element.getAttribute('aria-label') || '';
    return `${label} ${name} ${placeholder} ${ariaLabel}`.toLowerCase();
  }

  getFieldLabel(element) {
    // Check for explicit label
    if (element.id) {
      const label = document.querySelector(`label[for="${element.id}"]`);
      if (label) return label.textContent.trim();
    }
    
    // Check parent for label
    const parent = element.closest('.form-group, .field, label');
    if (parent) {
      const label = parent.querySelector('label, .label');
      if (label && label !== element) return label.textContent.trim();
    }
    
    // Check previous sibling
    const prev = element.previousElementSibling;
    if (prev?.tagName === 'LABEL') return prev.textContent.trim();
    
    return element.placeholder || element.name || '';
  }

  async autoFillForm() {
    if (!this.userProfile) {
      this.showToast('Please sync your ScholarStream profile first', 'error');
      return { success: false };
    }

    let filledCount = 0;
    const fillField = (fields, value) => {
      fields.forEach(field => {
        if (value) {
          field.element.value = value;
          this.triggerInput(field.element);
          field.element.classList.add('ss-highlight-field');
          filledCount++;
        }
      });
    };

    // Map profile data to fields
    const profile = this.userProfile;
    
    fillField(this.fields.name, profile.full_name || profile.name);
    fillField(this.fields.email, profile.email);
    fillField(this.fields.phone, profile.phone);
    fillField(this.fields.school, profile.school || profile.university);
    fillField(this.fields.gpa, profile.gpa?.toString());
    fillField(this.fields.major, profile.major || profile.field_of_study);
    fillField(this.fields.year, profile.graduation_year || profile.academic_year);
    
    // Handle address fields
    if (this.fields.address.length > 0 && profile.address) {
      fillField(this.fields.address, profile.address);
    }

    // Track this application
    await this.trackApplication();

    this.showToast(`✅ Auto-filled ${filledCount} fields!`, 'success');
    
    // Remove highlights after 3 seconds
    setTimeout(() => {
      document.querySelectorAll('.ss-highlight-field').forEach(el => {
        el.classList.remove('ss-highlight-field');
      });
    }, 3000);

    return { success: true, filled: filledCount };
  }

  triggerInput(element) {
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
    element.dispatchEvent(new Event('blur', { bubbles: true }));
  }

  async openEssayAssistant() {
    if (this.fields.essay.length === 0) {
      this.showToast('No essay fields detected on this page', 'error');
      return;
    }

    this.showEssayModal();
  }

  showEssayModal() {
    if (document.getElementById('ss-essay-modal')) return;
    
    const essayField = this.fields.essay[0];
    const currentText = essayField.element.value || '';
    const wordCount = this.countWords(currentText);
    
    const modal = document.createElement('div');
    modal.id = 'ss-essay-modal';
    modal.className = 'ss-fade-in';
    modal.innerHTML = `
      <div class="essay-modal-backdrop"></div>
      <div class="essay-modal">
        <div class="essay-modal-header">
          <h2>✍️ AI Essay Assistant</h2>
          <button class="close-btn" id="ss-close-essay">×</button>
        </div>
        
        <div class="essay-prompt-section">
          <h4>Essay Prompt</h4>
          <p class="essay-prompt-text">${essayField.prompt || 'Write your response below'}</p>
          ${essayField.maxLength ? `<span class="word-limit">Max: ${essayField.maxLength} characters</span>` : ''}
        </div>
        
        <div class="essay-tabs">
          <button class="tab active" data-tab="generate">Generate</button>
          <button class="tab" data-tab="improve">Improve</button>
          <button class="tab" data-tab="research">Research</button>
        </div>
        
        <div class="tab-content active" id="tab-generate">
          <div class="tone-selector">
            <label>Writing Tone:</label>
            <select id="ss-essay-tone">
              <option value="authentic">Authentic & Personal</option>
              <option value="professional">Professional</option>
              <option value="passionate">Passionate</option>
              <option value="reflective">Reflective</option>
            </select>
          </div>
          
          <div class="additional-context">
            <label>Additional Context (optional):</label>
            <textarea id="ss-additional-context" placeholder="Any specific experiences, achievements, or points you want to include..."></textarea>
          </div>
          
          <button class="btn-primary btn-lg" id="ss-generate-essay">
            <span class="btn-icon">✨</span>
            Generate Essay Draft
          </button>
        </div>
        
        <div class="tab-content" id="tab-improve">
          <div class="current-text">
            <label>Current Essay (${wordCount} words):</label>
            <textarea id="ss-current-essay" placeholder="Paste or type your current essay here...">${currentText}</textarea>
          </div>
          
          <div class="improve-options">
            <label>What to improve:</label>
            <div class="checkbox-group">
              <label><input type="checkbox" value="clarity" checked> Clarity</label>
              <label><input type="checkbox" value="voice"> Stronger Voice</label>
              <label><input type="checkbox" value="examples"> Better Examples</label>
              <label><input type="checkbox" value="flow"> Flow & Structure</label>
            </div>
          </div>
          
          <button class="btn-primary btn-lg" id="ss-improve-essay">
            <span class="btn-icon">🔧</span>
            Improve Essay
          </button>
        </div>
        
        <div class="tab-content" id="tab-research">
          <div class="research-topic">
            <label>Research Topic:</label>
            <input type="text" id="ss-research-topic" placeholder="Enter a topic to research for your essay...">
          </div>
          
          <button class="btn-secondary btn-lg" id="ss-do-research">
            <span class="btn-icon">🔍</span>
            Get Research & Insights
          </button>
          
          <div class="research-results" id="ss-research-results"></div>
        </div>
        
        <div class="essay-output" id="ss-essay-output" style="display: none;">
          <div class="output-header">
            <h4>Generated Content</h4>
            <div class="output-actions">
              <button class="btn-sm" id="ss-copy-essay">📋 Copy</button>
              <button class="btn-sm" id="ss-insert-essay">📝 Insert</button>
              <button class="btn-sm" id="ss-regenerate">🔄 Regenerate</button>
            </div>
          </div>
          <div class="output-content" id="ss-output-text"></div>
          <div class="output-stats">
            <span id="ss-output-words">0 words</span>
            <span id="ss-output-chars">0 characters</span>
          </div>
        </div>
        
        <div class="essay-tips">
          <h4>💡 Quick Tips</h4>
          <ul>
            <li>Be specific - use real names, dates, and places</li>
            <li>Show vulnerability - mention challenges and growth</li>
            <li>Avoid clichés like "I've always been passionate about..."</li>
            <li>End with forward momentum, not a summary</li>
          </ul>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    this.attachEssayModalListeners(essayField);
  }

  attachEssayModalListeners(essayField) {
    // Close modal
    document.getElementById('ss-close-essay')?.addEventListener('click', () => {
      document.getElementById('ss-essay-modal')?.remove();
    });
    
    document.querySelector('.essay-modal-backdrop')?.addEventListener('click', () => {
      document.getElementById('ss-essay-modal')?.remove();
    });
    
    // Tab switching
    document.querySelectorAll('.essay-tabs .tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        document.querySelectorAll('.essay-tabs .tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        e.target.classList.add('active');
        document.getElementById(`tab-${e.target.dataset.tab}`)?.classList.add('active');
      });
    });
    
    // Generate essay
    document.getElementById('ss-generate-essay')?.addEventListener('click', async () => {
      await this.generateEssay(essayField);
    });
    
    // Improve essay
    document.getElementById('ss-improve-essay')?.addEventListener('click', async () => {
      await this.improveEssay();
    });
    
    // Research
    document.getElementById('ss-do-research')?.addEventListener('click', async () => {
      await this.doResearch();
    });
    
    // Copy essay
    document.getElementById('ss-copy-essay')?.addEventListener('click', () => {
      const text = document.getElementById('ss-output-text')?.textContent;
      navigator.clipboard.writeText(text);
      this.showToast('Copied to clipboard!', 'success');
    });
    
    // Insert essay
    document.getElementById('ss-insert-essay')?.addEventListener('click', () => {
      const text = document.getElementById('ss-output-text')?.textContent;
      essayField.element.value = text;
      this.triggerInput(essayField.element);
      this.showToast('Essay inserted!', 'success');
      document.getElementById('ss-essay-modal')?.remove();
    });
    
    // Regenerate
    document.getElementById('ss-regenerate')?.addEventListener('click', async () => {
      await this.generateEssay(essayField);
    });
  }

  async generateEssay(essayField) {
    const tone = document.getElementById('ss-essay-tone')?.value || 'authentic';
    const additionalContext = document.getElementById('ss-additional-context')?.value || '';
    const outputArea = document.getElementById('ss-essay-output');
    const outputText = document.getElementById('ss-output-text');
    
    // Show loading state
    outputArea.style.display = 'block';
    outputText.innerHTML = `
      <div class="generating">
        <div class="ss-typing"><span></span><span></span><span></span></div>
        <p>Generating your essay draft...</p>
      </div>
    `;
    
    const prompt = `Write a compelling essay for this prompt: "${essayField.prompt}"
                    
Additional context from the applicant: ${additionalContext}

The essay should be ${essayField.maxLength ? `under ${essayField.maxLength} characters` : 'around 500 words'}.`;
    
    const result = await chrome.runtime.sendMessage({
      action: 'generateEssay',
      prompt: prompt,
      context: this.currentOpportunity,
      tone: tone
    });
    
    if (result.success) {
      outputText.textContent = result.essay;
      document.getElementById('ss-output-words').textContent = `${result.word_count || this.countWords(result.essay)} words`;
      document.getElementById('ss-output-chars').textContent = `${result.essay.length} characters`;
    } else {
      outputText.innerHTML = `
        <div class="error">
          <p>⚠️ ${result.error || 'Generation failed. Please try again.'}</p>
          ${result.fallback_tips ? `
            <div class="fallback-tips">
              <h5>Writing Tips:</h5>
              <ul>${result.fallback_tips.map(tip => `<li>${tip}</li>`).join('')}</ul>
            </div>
          ` : ''}
        </div>
      `;
    }
  }

  async improveEssay() {
    const currentEssay = document.getElementById('ss-current-essay')?.value;
    if (!currentEssay) {
      this.showToast('Please enter your current essay first', 'error');
      return;
    }
    
    const improvements = Array.from(document.querySelectorAll('#tab-improve .checkbox-group input:checked'))
      .map(cb => cb.value);
    
    const outputArea = document.getElementById('ss-essay-output');
    const outputText = document.getElementById('ss-output-text');
    
    outputArea.style.display = 'block';
    outputText.innerHTML = `
      <div class="generating">
        <div class="ss-typing"><span></span><span></span><span></span></div>
        <p>Improving your essay...</p>
      </div>
    `;
    
    const result = await chrome.runtime.sendMessage({
      action: 'improveText',
      text: currentEssay,
      instructions: `Focus on improving: ${improvements.join(', ')}`
    });
    
    if (result.success) {
      outputText.textContent = result.improved_text;
      document.getElementById('ss-output-words').textContent = `${this.countWords(result.improved_text)} words`;
      document.getElementById('ss-output-chars').textContent = `${result.improved_text.length} characters`;
    } else {
      outputText.innerHTML = `<div class="error">⚠️ ${result.error || 'Improvement failed'}</div>`;
    }
  }

  async doResearch() {
    const topic = document.getElementById('ss-research-topic')?.value;
    if (!topic) {
      this.showToast('Please enter a topic to research', 'error');
      return;
    }
    
    const resultsArea = document.getElementById('ss-research-results');
    resultsArea.innerHTML = `
      <div class="generating">
        <div class="ss-typing"><span></span><span></span><span></span></div>
        <p>Researching "${topic}"...</p>
      </div>
    `;
    
    const result = await chrome.runtime.sendMessage({
      action: 'researchTopic',
      topic: topic,
      opportunityContext: this.currentOpportunity
    });
    
    if (result.success) {
      resultsArea.innerHTML = `
        <div class="research-content">
          <h5>Research Results for "${topic}"</h5>
          <div class="research-text">${this.formatResearch(result.research)}</div>
        </div>
      `;
    } else {
      resultsArea.innerHTML = `
        <div class="research-content">
          <h5>Research Tips</h5>
          <div class="research-text">${result.fallback || 'Research unavailable'}</div>
        </div>
      `;
    }
  }

  formatResearch(text) {
    // Convert markdown-like formatting to HTML
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>')
      .replace(/^/, '<p>')
      .replace(/$/, '</p>');
  }

  async showWinningTips() {
    const panel = document.getElementById('scholarstream-copilot-panel');
    if (!panel) return;
    
    const tipsContainer = panel.querySelector('.copilot-actions');
    tipsContainer.innerHTML = `
      <div class="loading-tips">
        <div class="ss-typing"><span></span><span></span><span></span></div>
        <p>Loading winning tips...</p>
      </div>
    `;
    
    const result = await chrome.runtime.sendMessage({
      action: 'getWinningTips',
      opportunityType: this.currentOpportunity?.type || 'scholarship',
      organization: this.currentOpportunity?.organization || 'this organization'
    });
    
    const tips = result.success ? result.tips : result.fallback?.join('\n• ') || 'Tips unavailable';
    
    tipsContainer.innerHTML = `
      <div class="winning-tips-content">
        <h4>🏆 Winning Tips for ${this.currentOpportunity?.organization || 'This Application'}</h4>
        <div class="tips-text">${this.formatResearch(tips)}</div>
        <button class="btn-secondary" id="ss-back-to-actions">← Back</button>
      </div>
    `;
    
    document.getElementById('ss-back-to-actions')?.addEventListener('click', () => {
      this.showCopilotPanel();
    });
  }

  async trackApplication() {
    const application = {
      ...this.currentOpportunity,
      status: 'in_progress',
      tracked_at: new Date().toISOString()
    };
    
    await chrome.runtime.sendMessage({
      action: 'trackApplication',
      application: application
    });
    
    this.showToast('Application tracked!', 'success');
    return { success: true };
  }

  async showImprovedTextModal(original, improved) {
    const modal = document.createElement('div');
    modal.id = 'ss-improved-modal';
    modal.className = 'ss-fade-in';
    modal.innerHTML = `
      <div class="essay-modal-backdrop"></div>
      <div class="improved-modal">
        <div class="essay-modal-header">
          <h2>✨ Improved Text</h2>
          <button class="close-btn" id="ss-close-improved">×</button>
        </div>
        <div class="comparison">
          <div class="original">
            <h4>Original</h4>
            <p>${original}</p>
          </div>
          <div class="improved">
            <h4>Improved</h4>
            <p>${improved}</p>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" id="ss-copy-improved">📋 Copy Improved</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    document.getElementById('ss-close-improved')?.addEventListener('click', () => modal.remove());
    document.querySelector('#ss-improved-modal .essay-modal-backdrop')?.addEventListener('click', () => modal.remove());
    document.getElementById('ss-copy-improved')?.addEventListener('click', () => {
      navigator.clipboard.writeText(improved);
      this.showToast('Copied!', 'success');
    });
    
    return { success: true };
  }

  async showResearchPanel(topic, research) {
    const modal = document.createElement('div');
    modal.id = 'ss-research-modal';
    modal.className = 'ss-fade-in';
    modal.innerHTML = `
      <div class="essay-modal-backdrop"></div>
      <div class="research-modal">
        <div class="essay-modal-header">
          <h2>🔍 Research: ${topic}</h2>
          <button class="close-btn" id="ss-close-research">×</button>
        </div>
        <div class="research-content">
          ${this.formatResearch(research)}
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    document.getElementById('ss-close-research')?.addEventListener('click', () => modal.remove());
    document.querySelector('#ss-research-modal .essay-modal-backdrop')?.addEventListener('click', () => modal.remove());
    
    return { success: true };
  }

  countWords(text) {
    if (!text) return 0;
    return text.trim().split(/\s+/).filter(w => w.length > 0).length;
  }

  async getUserProfile() {
    return new Promise((resolve) => {
      chrome.storage.sync.get(['userProfile'], (result) => {
        resolve(result.userProfile);
      });
    });
  }

  showToast(message, type = 'success') {
    // Remove existing toasts
    document.querySelectorAll('.scholarstream-toast').forEach(t => t.remove());
    
    const toast = document.createElement('div');
    toast.className = `scholarstream-toast toast-${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
      <span class="toast-message">${message}</span>
    `;
    document.body.appendChild(toast);

    requestAnimationFrame(() => {
      toast.classList.add('show');
    });

    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }
}

// Initialize when page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new ScholarStreamCopilot());
} else {
  new ScholarStreamCopilot();
}
