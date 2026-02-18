/**
 * ScholarStream Copilot - Enhanced Content Script
 * Detects scholarship application forms and provides AI-powered auto-fill
 */

const SCHOLARSTREAM_API = 'https://scholarstream-backend.onrender.com';

let copilotSidebar = null;
let userProfile = null;
let detectedFormFields = [];

const FORM_INDICATORS = [
  'application', 'apply', 'scholarship', 'grant', 'hackathon',
  'bounty', 'competition', 'register', 'submit', 'entry'
];

const FORM_PLATFORMS = [
  'scholarships.com', 'fastweb.com', 'niche.com',
  'devpost.com', 'mlh.io', 'kaggle.com',
  'gitcoin.co', 'submittable.com', 'apply.org'
];

function isApplicationPage() {
  const url = window.location.href.toLowerCase();
  const title = document.title.toLowerCase();
  const bodyText = document.body.innerText.toLowerCase().substring(0, 1000);

  const isPlatform = FORM_PLATFORMS.some(platform => url.includes(platform));

  const hasIndicator = FORM_INDICATORS.some(indicator =>
    url.includes(indicator) || title.includes(indicator) || bodyText.includes(indicator)
  );

  const hasForms = document.querySelectorAll('form').length > 0;
  const hasInputs = document.querySelectorAll('input, textarea').length > 3;

  return (isPlatform && hasForms) || (hasIndicator && hasInputs);
}

function detectFormFields() {
  const formFields = [];

  const inputs = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"])');
  const textareas = document.querySelectorAll('textarea');
  const selects = document.querySelectorAll('select');

  [...inputs, ...textareas, ...selects].forEach((field, index) => {
    const fieldInfo = {
      id: field.id || `field_${index}`,
      name: field.name || field.id || `unnamed_${index}`,
      type: field.type || field.tagName.toLowerCase(),
      selector: generateSelector(field),
      label: getFieldLabel(field),
      placeholder: field.placeholder || '',
      required: field.required,
      value: field.value
    };

    if (fieldInfo.label || fieldInfo.placeholder || fieldInfo.name) {
      formFields.push(fieldInfo);
    }
  });

  console.log(`Detected ${formFields.length} form fields`);
  return formFields;
}

function generateSelector(element) {
  if (element.id) {
    return `#${element.id}`;
  }

  if (element.name) {
    return `[name="${element.name}"]`;
  }

  let path = [];
  let current = element;

  while (current && current !== document.body) {
    let selector = current.tagName.toLowerCase();

    if (current.className) {
      const classes = current.className.split(' ').filter(c => c.trim()).slice(0, 2);
      if (classes.length > 0) {
        selector += '.' + classes.join('.');
      }
    }

    path.unshift(selector);
    current = current.parentElement;

    if (path.length >= 3) break;
  }

  return path.join(' > ');
}

function getFieldLabel(field) {
  if (field.labels && field.labels.length > 0) {
    return field.labels[0].innerText.trim();
  }

  const labelFor = document.querySelector(`label[for="${field.id}"]`);
  if (labelFor) {
    return labelFor.innerText.trim();
  }

  const closestLabel = field.closest('label');
  if (closestLabel) {
    return closestLabel.innerText.replace(field.value, '').trim();
  }

  const precedingLabel = field.previousElementSibling;
  if (precedingLabel && precedingLabel.tagName === 'LABEL') {
    return precedingLabel.innerText.trim();
  }

  const parentLabel = field.parentElement?.innerText;
  if (parentLabel && parentLabel.length < 100) {
    return parentLabel.replace(field.value, '').trim();
  }

  return '';
}

async function getUserProfile() {
  try {
    const response = await fetch(`${SCHOLARSTREAM_API}/api/extension/user-profile`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await getAuthToken()}`
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch profile: ${response.status}`);
    }

    const data = await response.json();
    return data.profile;
  } catch (error) {
    console.error('Error fetching user profile:', error);
    return null;
  }
}

async function mapFormFields(formFields, userProfile) {
  try {
    const response = await fetch(`${SCHOLARSTREAM_API}/api/extension/map-fields`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await getAuthToken()}`
      },
      body: JSON.stringify({
        form_fields: formFields,
        user_profile: userProfile
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to map fields: ${response.status}`);
    }

    const data = await response.json();
    return data.field_mappings;
  } catch (error) {
    console.error('Error mapping form fields:', error);
    return {};
  }
}

async function getAuthToken() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['authToken'], (result) => {
      resolve(result.authToken || '');
    });
  });
}

function createCopilotSidebar() {
  if (copilotSidebar) return;

  const sidebar = document.createElement('div');
  sidebar.id = 'scholarstream-copilot';
  sidebar.innerHTML = `
    <div class="copilot-header">
      <div class="copilot-logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2"/>
          <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2"/>
          <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2"/>
        </svg>
        <span>ScholarStream</span>
      </div>
      <button class="copilot-close" onclick="document.getElementById('scholarstream-copilot').remove()">×</button>
    </div>
    <div class="copilot-body">
      <h3>Application Co-Pilot</h3>
      <p>AI-powered form filling to save you time</p>
      <button id="scan-and-fill-btn" class="btn-primary">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M21 21L15 15M17 10C17 13.866 13.866 17 10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10Z" stroke="currentColor" stroke-width="2"/>
        </svg>
        Scan Page & Autofill
      </button>
      <div id="copilot-status" class="status-idle">
        <span class="status-icon">●</span>
        <span class="status-text">Ready to scan</span>
      </div>
      <div id="copilot-results" class="results-container"></div>
    </div>
  `;

  document.body.appendChild(sidebar);
  copilotSidebar = sidebar;

  document.getElementById('scan-and-fill-btn').addEventListener('click', handleScanAndFill);
}

async function handleScanAndFill() {
  const statusEl = document.getElementById('copilot-status');
  const resultsEl = document.getElementById('copilot-results');
  const btnEl = document.getElementById('scan-and-fill-btn');

  btnEl.disabled = true;
  setStatus('Scanning page...', 'loading');
  resultsEl.innerHTML = '';

  detectedFormFields = detectFormFields();

  if (detectedFormFields.length === 0) {
    setStatus('No form fields detected', 'error');
    btnEl.disabled = false;
    return;
  }

  setStatus(`Found ${detectedFormFields.length} fields, fetching your profile...`, 'loading');

  userProfile = await getUserProfile();

  if (!userProfile) {
    setStatus('Please log in to ScholarStream first', 'error');
    resultsEl.innerHTML = `
      <div class="error-message">
        <p>You need to be logged in to use auto-fill.</p>
        <a href="https://scholarstream-v3.vercel.app/login" target="_blank" class="btn-link">Log In</a>
      </div>
    `;
    btnEl.disabled = false;
    return;
  }

  setStatus('Mapping fields with AI...', 'loading');

  const fieldMappings = await mapFormFields(detectedFormFields, userProfile);

  if (Object.keys(fieldMappings).length === 0) {
    setStatus('No fields could be auto-filled', 'error');
    btnEl.disabled = false;
    return;
  }

  setStatus(`Ready to fill ${Object.keys(fieldMappings).length} fields`, 'success');

  displayFieldMappings(fieldMappings);

  btnEl.disabled = false;
}

function displayFieldMappings(fieldMappings) {
  const resultsEl = document.getElementById('copilot-results');

  resultsEl.innerHTML = `
    <div class="mappings-header">
      <h4>Suggested Values</h4>
      <p class="helper-text">Click to copy, or use the "Fill All" button</p>
    </div>
    <div class="mappings-list"></div>
    <button id="fill-all-btn" class="btn-secondary">Fill All Fields</button>
  `;

  const listEl = resultsEl.querySelector('.mappings-list');

  Object.entries(fieldMappings).forEach(([selector, value]) => {
    const field = detectedFormFields.find(f => f.selector === selector);

    const mappingEl = document.createElement('div');
    mappingEl.className = 'mapping-item';
    mappingEl.innerHTML = `
      <div class="mapping-label">${field?.label || field?.name || 'Field'}</div>
      <div class="mapping-value">
        <input type="text" value="${escapeHtml(value)}" readonly />
        <button class="btn-copy" data-selector="${selector}" data-value="${escapeHtml(value)}">
          Copy
        </button>
        <button class="btn-fill" data-selector="${selector}" data-value="${escapeHtml(value)}">
          Fill
        </button>
      </div>
    `;

    listEl.appendChild(mappingEl);
  });

  listEl.querySelectorAll('.btn-copy').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const value = e.target.getAttribute('data-value');
      navigator.clipboard.writeText(value);
      e.target.textContent = 'Copied!';
      setTimeout(() => { e.target.textContent = 'Copy'; }, 2000);
    });
  });

  listEl.querySelectorAll('.btn-fill').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const selector = e.target.getAttribute('data-selector');
      const value = e.target.getAttribute('data-value');
      fillField(selector, value);
      e.target.textContent = 'Filled!';
      e.target.classList.add('filled');
    });
  });

  document.getElementById('fill-all-btn').addEventListener('click', () => {
    Object.entries(fieldMappings).forEach(([selector, value]) => {
      fillField(selector, value);
    });

    setStatus('All fields filled!', 'success');
  });
}

function fillField(selector, value) {
  try {
    const field = document.querySelector(selector);

    if (!field) {
      console.warn(`Field not found: ${selector}`);
      return;
    }

    field.value = value;

    field.dispatchEvent(new Event('input', { bubbles: true }));
    field.dispatchEvent(new Event('change', { bubbles: true }));

    field.style.backgroundColor = '#d4edda';
    setTimeout(() => {
      field.style.backgroundColor = '';
    }, 2000);

    console.log(`Filled field: ${selector}`);
  } catch (error) {
    console.error(`Error filling field ${selector}:`, error);
  }
}

function setStatus(text, state) {
  const statusEl = document.getElementById('copilot-status');
  statusEl.className = `status-${state}`;
  statusEl.querySelector('.status-text').textContent = text;
}

function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

function init() {
  if (isApplicationPage()) {
    console.log('ScholarStream Copilot: Application page detected');

    setTimeout(() => {
      createCopilotSidebar();
    }, 1500);
  } else {
    console.log('ScholarStream Copilot: Not an application page');
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'toggleCopilot') {
    if (copilotSidebar) {
      copilotSidebar.remove();
      copilotSidebar = null;
    } else {
      createCopilotSidebar();
    }
  }
});
