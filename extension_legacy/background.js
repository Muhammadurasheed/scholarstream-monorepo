/**
 * ScholarStream Copilot - Background Service Worker
 * Handles extension logic, AI essay generation, and web research
 */

const BACKEND_URL = 'https://scholarstream-backend.onrender.com';
const WEB_APP_URL = 'https://scholarstream-v3.vercel.app';

// Listen for extension installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('[ScholarStream Copilot] Extension installed successfully');
  
  // Create context menus
  chrome.contextMenus.create({
    id: 'scholarstream-autofill',
    title: 'Auto-fill with ScholarStream',
    contexts: ['editable']
  });
  
  chrome.contextMenus.create({
    id: 'scholarstream-improve-text',
    title: 'Improve this text with AI',
    contexts: ['selection']
  });
  
  chrome.contextMenus.create({
    id: 'scholarstream-research',
    title: 'Research this topic',
    contexts: ['selection']
  });
});

// Listen for messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // Handle async responses
  handleMessage(request, sender).then(sendResponse);
  return true;
});

async function handleMessage(request, sender) {
  switch (request.action) {
    case 'syncProfile':
      return syncProfile(request.profile);
    
    case 'getProfile':
      return getProfile();
    
    case 'trackApplication':
      return trackApplication(request.application);
    
    case 'generateEssay':
      return generateEssay(request.prompt, request.context, request.tone);
    
    case 'improveText':
      return improveText(request.text, request.instructions);
    
    case 'researchTopic':
      return researchTopic(request.topic, request.opportunityContext);
    
    case 'getWinningTips':
      return getWinningTips(request.opportunityType, request.organization);
    
    case 'checkGrammar':
      return checkGrammar(request.text);
    
    case 'getApplicationStats':
      return getApplicationStats();
    
    default:
      return { error: 'Unknown action' };
  }
}

// ============= Profile Management =============

async function syncProfile(profile) {
  try {
    await chrome.storage.sync.set({ userProfile: profile });
    console.log('[ScholarStream] Profile synced successfully');
    return { success: true };
  } catch (error) {
    console.error('[ScholarStream] Profile sync failed:', error);
    return { success: false, error: error.message };
  }
}

async function getProfile() {
  try {
    const result = await chrome.storage.sync.get(['userProfile']);
    return { profile: result.userProfile };
  } catch (error) {
    return { profile: null, error: error.message };
  }
}

// ============= Application Tracking =============

async function trackApplication(application) {
  try {
    const result = await chrome.storage.local.get(['applications']);
    const applications = result.applications || [];
    
    // Check for duplicates
    const exists = applications.some(app => app.url === application.url);
    if (!exists) {
      applications.push({
        ...application,
        tracked_at: new Date().toISOString()
      });
      await chrome.storage.local.set({ applications });
    }
    
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function getApplicationStats() {
  try {
    const result = await chrome.storage.local.get(['applications']);
    const applications = result.applications || [];
    
    return {
      total: applications.length,
      in_progress: applications.filter(a => a.status === 'in_progress').length,
      submitted: applications.filter(a => a.status === 'submitted').length,
      applications: applications.slice(-10) // Last 10
    };
  } catch (error) {
    return { total: 0, in_progress: 0, submitted: 0, applications: [] };
  }
}

// ============= AI Essay Generation =============

async function generateEssay(prompt, context, tone = 'authentic') {
  try {
    const profile = (await chrome.storage.sync.get(['userProfile'])).userProfile;
    
    if (!profile) {
      return { error: 'Please sync your ScholarStream profile first' };
    }
    
    // Build comprehensive context from user profile
    const userContext = buildUserContext(profile);
    
    // System prompt for natural, human-like writing
    const systemPrompt = buildEssaySystemPrompt(tone, userContext);
    
    const response = await fetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: prompt,
        context: {
          type: 'essay_generation',
          user_profile: userContext,
          opportunity_context: context,
          tone: tone
        },
        system_prompt: systemPrompt
      })
    });
    
    if (!response.ok) {
      throw new Error('Essay generation failed');
    }
    
    const data = await response.json();
    
    return {
      success: true,
      essay: data.response || data.message,
      tips: data.tips || [],
      word_count: countWords(data.response || data.message)
    };
  } catch (error) {
    console.error('[ScholarStream] Essay generation error:', error);
    
    // Fallback to local generation hints
    return {
      success: false,
      error: error.message,
      fallback_tips: getLocalEssayTips(prompt)
    };
  }
}

function buildUserContext(profile) {
  return {
    name: profile.name || profile.full_name,
    academic: {
      school: profile.school || profile.university,
      major: profile.major || profile.field_of_study,
      gpa: profile.gpa,
      year: profile.graduation_year || profile.academic_year,
      level: profile.academic_level // undergraduate, graduate, etc.
    },
    background: {
      ethnicity: profile.ethnicity,
      first_gen: profile.first_generation,
      citizenship: profile.citizenship,
      state: profile.state,
      city: profile.city
    },
    interests: profile.interests || [],
    skills: profile.skills || [],
    experiences: profile.experiences || [],
    goals: profile.goals || profile.career_goals,
    achievements: profile.achievements || [],
    challenges: profile.challenges_overcome || [],
    motivation: profile.motivation // urgent vs long-term
  };
}

function buildEssaySystemPrompt(tone, userContext) {
  const toneGuides = {
    authentic: `Write in a genuine, personal voice. Use specific details and anecdotes from the user's life. 
                Avoid clichés, generic phrases, and overly formal language. 
                The essay should sound like a real person sharing their story, not an AI.`,
    professional: `Write in a polished but warm professional tone. 
                   Balance formality with personality. Use concrete examples.`,
    passionate: `Write with energy and enthusiasm. Show deep commitment to the topic.
                 Use vivid language and powerful examples. Let emotion come through naturally.`,
    reflective: `Write thoughtfully, showing growth and self-awareness.
                Focus on lessons learned and personal development.`
  };
  
  return `You are a skilled writing mentor helping a student craft a compelling scholarship/application essay.

YOUR MISSION: Help ${userContext.name} write an essay that is authentically THEIRS - not AI-generated sounding.

CRITICAL RULES FOR HUMAN-LIKE WRITING:
1. NEVER use phrases like "I am passionate about", "I have always been", "since childhood", "my journey"
2. NEVER start sentences with "Furthermore", "Moreover", "Additionally", "In conclusion"
3. AVOID perfect grammar - real humans use contractions, start sentences with "And" or "But"
4. Include SPECIFIC details: names, dates, places, sensory descriptions
5. Show vulnerability - mention doubts, failures, learning moments
6. Use conversational language - write like you're telling a friend
7. Vary sentence length dramatically - mix short punchy sentences with longer flowing ones
8. Include ONE unexpected detail or humor if appropriate
9. End with forward-looking energy, not a summary

USER BACKGROUND TO INCORPORATE:
- School: ${userContext.academic.school || 'Not specified'}
- Major: ${userContext.academic.major || 'Not specified'}
- Interests: ${userContext.interests.join(', ') || 'Not specified'}
- Goals: ${userContext.goals || 'Not specified'}
- Key experiences: ${userContext.experiences.slice(0, 3).join('; ') || 'Not specified'}

TONE: ${toneGuides[tone] || toneGuides.authentic}

IMPORTANT: The essay must feel like it was written by a real student at 2am, not generated by AI.
Include imperfections that make it human. Reference real details from their profile.`;
}

function countWords(text) {
  if (!text) return 0;
  return text.trim().split(/\s+/).filter(w => w.length > 0).length;
}

function getLocalEssayTips(prompt) {
  const tips = [
    "Start with a specific moment or scene, not a general statement",
    "Show, don't tell - use concrete examples instead of adjectives",
    "Connect your past experiences to your future goals",
    "Be specific about what you learned, not just what you did",
    "End with forward momentum - what will you do next?"
  ];
  return tips;
}

// ============= Text Improvement =============

async function improveText(text, instructions = '') {
  try {
    const profile = (await chrome.storage.sync.get(['userProfile'])).userProfile;
    
    const response = await fetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: `Improve this text while keeping the author's voice and making it sound MORE human, not less. 
                  Keep contractions, casual language, and personality.
                  ${instructions ? `Additional instructions: ${instructions}` : ''}
                  
                  TEXT TO IMPROVE:
                  ${text}`,
        context: {
          type: 'text_improvement',
          preserve_voice: true
        }
      })
    });
    
    if (!response.ok) throw new Error('Text improvement failed');
    
    const data = await response.json();
    return {
      success: true,
      improved_text: data.response || data.message,
      changes_made: data.changes || []
    };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// ============= Research & Tips =============

async function researchTopic(topic, opportunityContext = {}) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: `Research and provide key insights about: ${topic}
                  
                  Context: This is for a ${opportunityContext.type || 'scholarship'} application 
                  to ${opportunityContext.organization || 'an organization'}.
                  
                  Provide:
                  1. Key facts and statistics
                  2. Recent developments or news
                  3. Why this topic matters
                  4. How to connect personal experience to this topic
                  5. Unique angles most applicants miss`,
        context: {
          type: 'research',
          opportunity: opportunityContext
        }
      })
    });
    
    if (!response.ok) throw new Error('Research failed');
    
    const data = await response.json();
    return {
      success: true,
      research: data.response || data.message,
      sources: data.sources || []
    };
  } catch (error) {
    return { 
      success: false, 
      error: error.message,
      fallback: getFallbackResearchTips(topic)
    };
  }
}

async function getWinningTips(opportunityType, organization) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: `Provide winning application tips for a ${opportunityType} from ${organization}.
                  
                  Include:
                  1. What this organization values most
                  2. Common mistakes to avoid
                  3. What makes applications stand out
                  4. Key phrases or themes to incorporate
                  5. Red flags that get applications rejected`,
        context: {
          type: 'winning_tips',
          opportunity_type: opportunityType,
          organization: organization
        }
      })
    });
    
    if (!response.ok) throw new Error('Tips fetch failed');
    
    const data = await response.json();
    return {
      success: true,
      tips: data.response || data.message
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      fallback: getGenericWinningTips(opportunityType)
    };
  }
}

function getFallbackResearchTips(topic) {
  return `Research tips for "${topic}":
  
1. Search for recent news articles (last 6 months)
2. Look for statistics from reputable sources
3. Find personal stories related to this topic
4. Identify key challenges and solutions
5. Note any controversies or debates`;
}

function getGenericWinningTips(type) {
  const tips = {
    scholarship: [
      "Demonstrate financial need with specific examples",
      "Show how you'll give back to your community",
      "Connect your major to your life experiences",
      "Be specific about how you'll use the funds",
      "Proofread multiple times - typos are automatic rejections"
    ],
    hackathon: [
      "Focus on problem-solving ability, not just coding skills",
      "Show teamwork and collaboration experience",
      "Highlight past projects with measurable impact",
      "Demonstrate creativity and innovative thinking",
      "Show enthusiasm for the specific hackathon theme"
    ],
    bounty: [
      "Demonstrate relevant technical skills clearly",
      "Show understanding of the problem space",
      "Reference similar work you've completed",
      "Be specific about your approach and timeline",
      "Highlight unique value you bring"
    ]
  };
  
  return tips[type] || tips.scholarship;
}

// ============= Grammar Check =============

async function checkGrammar(text) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: `Check this text for grammar, spelling, and clarity issues. 
                  Keep the author's voice - don't over-correct casual language if it's intentional.
                  
                  TEXT:
                  ${text}
                  
                  Return issues in format:
                  - Issue: [description]
                  - Suggestion: [fix]`,
        context: { type: 'grammar_check' }
      })
    });
    
    if (!response.ok) throw new Error('Grammar check failed');
    
    const data = await response.json();
    return {
      success: true,
      issues: data.response || data.message
    };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// ============= Context Menu Handlers =============

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  switch (info.menuItemId) {
    case 'scholarstream-autofill':
      chrome.tabs.sendMessage(tab.id, { action: 'autofill' });
      break;
    
    case 'scholarstream-improve-text':
      const improved = await improveText(info.selectionText);
      chrome.tabs.sendMessage(tab.id, { 
        action: 'showImprovedText', 
        original: info.selectionText,
        improved: improved.improved_text || info.selectionText
      });
      break;
    
    case 'scholarstream-research':
      const research = await researchTopic(info.selectionText);
      chrome.tabs.sendMessage(tab.id, { 
        action: 'showResearch', 
        topic: info.selectionText,
        research: research.research || research.fallback
      });
      break;
  }
});

// ============= External Communication =============

// Listen for messages from the web app
chrome.runtime.onMessageExternal.addListener(
  (request, sender, sendResponse) => {
    if (sender.origin === WEB_APP_URL || sender.origin.includes('localhost')) {
      handleMessage(request, sender).then(sendResponse);
      return true;
    }
  }
);
