/**
 * ScholarStream Copilot - Popup Script
 * Extension popup interface with profile sync
 */

document.addEventListener('DOMContentLoaded', async () => {
  await loadProfile();
  await loadStats();
  setupEventListeners();
});

async function loadProfile() {
  chrome.storage.sync.get(['userProfile', 'lastSync'], (result) => {
    const profile = result.userProfile;
    const lastSync = result.lastSync;
    const profileCard = document.getElementById('profileCard');
    const syncStatus = document.getElementById('syncStatus');
    const syncText = document.getElementById('syncText');
    
    if (profile) {
      document.getElementById('profileIcon').textContent = profile.name?.[0]?.toUpperCase() || 'U';
      document.getElementById('profileName').textContent = profile.name || 'User';
      document.getElementById('profileStatus').textContent = profile.school || profile.academic_status || 'Student';
      profileCard.classList.remove('not-signed-in');
      
      // Show sync status
      if (lastSync) {
        const syncDate = new Date(lastSync);
        const now = new Date();
        const diffMs = now - syncDate;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) {
          syncText.textContent = 'Just synced';
        } else if (diffMins < 60) {
          syncText.textContent = `Synced ${diffMins}m ago`;
        } else if (diffMins < 1440) {
          syncText.textContent = `Synced ${Math.floor(diffMins / 60)}h ago`;
        } else {
          syncText.textContent = `Synced ${Math.floor(diffMins / 1440)}d ago`;
        }
      } else {
        syncText.textContent = 'Profile synced';
      }
      syncStatus.classList.remove('error');
    } else {
      document.getElementById('profileIcon').textContent = '?';
      document.getElementById('profileName').textContent = 'Not signed in';
      document.getElementById('profileStatus').textContent = 'Sign in to ScholarStream →';
      profileCard.classList.add('not-signed-in');
      
      syncText.textContent = 'Not connected';
      syncStatus.classList.add('error');
    }
  });
}

async function loadStats() {
  chrome.storage.local.get(['applications', 'fieldsAutofilled'], (result) => {
    const applications = result.applications || [];
    const fieldsCount = result.fieldsAutofilled || 0;
    
    document.getElementById('appsTracked').textContent = applications.length;
    document.getElementById('fieldsAutofilled').textContent = fieldsCount;
  });
}

function setupEventListeners() {
  // Open dashboard button
  document.getElementById('openDashboard').addEventListener('click', () => {
    chrome.tabs.create({ url: 'https://scholarstream-v3.vercel.app/dashboard' });
  });
  
  // Sync profile button
  document.getElementById('syncProfileBtn').addEventListener('click', async () => {
    const btn = document.getElementById('syncProfileBtn');
    btn.textContent = 'Syncing...';
    btn.disabled = true;
    
    // Open ScholarStream profile page with sync parameter
    chrome.tabs.create({ 
      url: 'https://scholarstream-v3.vercel.app/profile?sync=extension',
      active: true
    });
    
    // Reset button after delay
    setTimeout(() => {
      btn.textContent = '↻ Sync Profile Now';
      btn.disabled = false;
      loadProfile();
    }, 3000);
  });
  
  // Profile card click - if not signed in, open login
  document.getElementById('profileCard').addEventListener('click', () => {
    chrome.storage.sync.get(['userProfile'], (result) => {
      if (!result.userProfile) {
        chrome.tabs.create({ url: 'https://scholarstream-v3.vercel.app/login' });
      }
    });
  });
}

// Listen for profile updates from the web app
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'profileUpdated') {
    loadProfile();
    sendResponse({ success: true });
  }
});
