import { Scholarship, UserProfile } from '@/types/scholarship';
import { differenceInDays } from 'date-fns';

/**
 * FAANG-Level Matching Engine
 * Multi-factor scoring system for hyper-personalized opportunity matching
 */

interface MatchScoreBreakdown {
  eligibility: number;
  interests: number;
  location: number;
  urgency: number;
  value: number;
  effort: number;
  total: number;
  explanation: string;
}

export class OpportunityMatchingEngine {
  private readonly weights = {
    eligibility: 30,  // Must meet basic requirements
    interests: 20,    // Alignment with user interests
    location: 15,     // Geographic relevance
    urgency: 15,      // Time-sensitive needs
    value: 10,        // Financial impact
    effort: 10        // Time to complete vs availability
  };

  // Interest-to-keyword mapping for intelligent matching (mirrors backend personalization_engine.py)
  // ENHANCED: Added DoraHacks, MLH, and broader tech keywords for better matching
  private readonly interestKeywords: Record<string, string[]> = {
    'artificial intelligence': ['ai', 'machine learning', 'deep learning', 'neural', 'nlp', 'gpt', 'llm', 'generative', 'ml', 'tensorflow', 'pytorch'],
    'ai': ['artificial intelligence', 'machine learning', 'deep learning', 'neural', 'nlp', 'gpt', 'llm', 'generative', 'ml', 'tensorflow', 'pytorch'],
    'web development': ['web', 'frontend', 'backend', 'fullstack', 'react', 'node', 'javascript', 'typescript', 'html', 'css', 'nextjs', 'vue', 'angular'],
    'blockchain': ['blockchain', 'crypto', 'web3', 'defi', 'nft', 'ethereum', 'solana', 'smart contract', 'dorahacks', 'buidl', 'dao'],
    'web3': ['blockchain', 'crypto', 'defi', 'nft', 'ethereum', 'solana', 'smart contract', 'decentralized', 'dorahacks', 'buidl', 'dao', 'dapp'],
    'cybersecurity': ['security', 'hacking', 'penetration', 'bug bounty', 'ctf', 'infosec', 'ethical hacking', 'intigriti', 'hackerone'],
    'data science': ['data', 'analytics', 'statistics', 'visualization', 'machine learning', 'big data', 'kaggle', 'pandas', 'numpy'],
    'mobile': ['mobile', 'ios', 'android', 'react native', 'flutter', 'swift', 'kotlin', 'app'],
    'game development': ['game', 'unity', '3d', 'unreal', 'gaming', 'gamedev'],
    'hackathons': ['hackathon', 'hack', 'build', 'competition', 'sprint', 'devpost', 'mlh', 'dorahacks', 'taikai', 'hackquest', 'buidl'],
    'software': ['software', 'engineering', 'developer', 'programming', 'code', 'tech', 'coding', 'algorithm', 'api'],
    'design': ['design', 'ui', 'ux', 'figma', 'product', 'creative', 'graphics'],
    'fintech': ['finance', 'banking', 'payments', 'trading', 'financial', 'defi'],
    'healthcare': ['healthcare', 'medical', 'biotech', 'health', 'telemedicine'],
    'entrepreneurship': ['startup', 'business', 'innovation', 'founder', 'venture', 'pitch'],
    'cloud': ['cloud', 'aws', 'azure', 'gcp', 'serverless', 'devops', 'kubernetes', 'docker'],
    // Added common student interests
    'coding': ['code', 'programming', 'developer', 'software', 'hackathon', 'algorithm', 'python', 'javascript'],
    'python': ['python', 'django', 'flask', 'pandas', 'numpy', 'data science', 'ml'],
    'open source': ['open source', 'github', 'contribution', 'oss', 'linux', 'community'],
  };

  /**
   * Calculate comprehensive match score (0-100)
   */
  calculateMatchScore(opportunity: Scholarship, profile: UserProfile): MatchScoreBreakdown {
    // DEBUG: Log inputs for first few items to diagnose 47% score issue
    if (Math.random() < 0.05) {
      console.log('Match Debug:', {
        opp: opportunity.name,
        oppTags: opportunity.tags,
        userInterests: profile.interests,
        userMajor: profile.major
      });
    }

    let score = 0;
    const breakdown: Partial<MatchScoreBreakdown> = {};

    // 0. STRICT EXPIRATION CHECK
    const daysUntil = this.getDaysUntilDeadline(opportunity.deadline);
    if (daysUntil < 0) {
      return {
        eligibility: 0,
        interests: 0,
        location: 0,
        urgency: 0,
        value: 0,
        effort: 0,
        total: 0,
        explanation: 'Opportunity has expired'
      };
    }

    // 1. ELIGIBILITY SCORE (30 points) - HARD REQUIREMENTS
    const eligibilityScore = this.scoreEligibility(opportunity, profile);

    // SOFTENED GATE: Only penalize, don't hard reject unless 0
    if (eligibilityScore === 0) {
      return {
        eligibility: 0,
        interests: 0,
        location: 0,
        urgency: 0,
        value: 0,
        effort: 0,
        total: 0,
        explanation: 'Does not meet strict eligibility'
      };
    }

    breakdown.eligibility = Math.round(eligibilityScore * this.weights.eligibility);
    score += breakdown.eligibility;

    // 2. INTERESTS ALIGNMENT (20 points)
    const interestScore = this.scoreInterests(opportunity, profile);
    breakdown.interests = Math.round(interestScore * this.weights.interests);
    score += breakdown.interests;

    // 3. LOCATION MATCH (15 points)
    const locationScore = this.scoreLocation(opportunity, profile);
    breakdown.location = Math.round(locationScore * this.weights.location);
    score += breakdown.location;

    // 4. URGENCY MATCH (15 points)
    const urgencyScore = this.scoreUrgency(opportunity, profile);
    breakdown.urgency = Math.round(urgencyScore * this.weights.urgency);
    score += breakdown.urgency;

    // 5. VALUE SCORE (10 points)
    const valueScore = this.scoreValue(opportunity, profile);
    breakdown.value = Math.round(valueScore * this.weights.value);
    score += breakdown.value;

    // 6. EFFORT FEASIBILITY (10 points)
    const effortScore = this.scoreEffort(opportunity, profile);
    breakdown.effort = Math.round(effortScore * this.weights.effort);
    score += breakdown.effort;

    breakdown.total = Math.round(score);
    breakdown.explanation = this.generateExplanation(breakdown as MatchScoreBreakdown, opportunity, profile);

    return breakdown as MatchScoreBreakdown;
  }

  private getDaysUntilDeadline(deadline: string): number {
    try {
      if (!deadline) return 365;
      const date = new Date(deadline);
      if (isNaN(date.getTime())) return 365;
      return differenceInDays(date, new Date());
    } catch (e) {
      return 365;
    }
  }

  private scoreEligibility(opp: Scholarship, profile: any): number {
    let score = 1.0;

    // Grade level matching
    const academicStatusMatch = {
      'High School': ['high school', 'freshman', 'sophomore', 'junior', 'senior', '12th grade', '11th grade'],
      'Undergraduate': ['undergraduate', 'college', 'university', 'bachelor'],
      'Graduate': ['graduate', 'masters', 'phd', 'doctoral'],
      'Postgraduate': ['postgraduate', 'post-doctoral']
    };

    const userStatus = profile.academicStatus || profile.academic_status || '';
    const oppTags = (opp.tags || []).map(t => t.toLowerCase());
    const oppEligibility = opp.eligibility?.grades_eligible || [];

    // Check explicit eligibility field first
    if (oppEligibility.length > 0) {
      const isEligible = oppEligibility.some((grade: string) =>
        userStatus.toLowerCase().includes(grade.toLowerCase())
      );
      if (!isEligible) score *= 0.5;
    } else {
      // Fallback to tags
      const expectedTags = academicStatusMatch[userStatus as keyof typeof academicStatusMatch] || [];
      const hasMatch = expectedTags.some(tag => oppTags.some(oppTag => oppTag.includes(tag)));

      if (!hasMatch && oppTags.length > 0) {
        score *= 0.7;
      }
    }

    return score;
  }

  private scoreInterests(opp: Scholarship, profile: any): number {
    const interests = profile.interests || [];

    if (!interests.length) {
      return 0.5; // Neutral if no user interests
    }

    // Step 1: Expand user interests with synonyms
    const expandedInterests = new Set<string>();
    for (const interest of interests) {
      const lowerInterest = interest.toLowerCase();
      expandedInterests.add(lowerInterest);

      // Add synonyms from our keyword map
      const synonyms = this.interestKeywords[lowerInterest] || [];
      synonyms.forEach(s => expandedInterests.add(s.toLowerCase()));
    }

    // Step 2: Build searchable text from opportunity (ENHANCED with more fields)
    const oppText = [
      ...(opp.tags || []),
      opp.name || '',
      opp.description || '',
      opp.organization || '',
      opp.source_url || '', // Include source for platform detection
    ].join(' ').toLowerCase();

    // Step 3: Count how many expanded interests match
    let matchCount = 0;
    const matchedKeywords: string[] = [];
    for (const keyword of expandedInterests) {
      if (oppText.includes(keyword)) {
        matchCount++;
        matchedKeywords.push(keyword);
      }
    }

    // Step 4: Calculate score with improved logic
    const ratio = matchCount / Math.max(3, expandedInterests.size);
    let score = Math.max(0.3, Math.min(ratio * 1.5, 1.0)); // Boost ratio by 1.5x

    // ENHANCED BONUS: Tech students should match with ALL hackathons
    const techInterests = ['software', 'coding', 'programming', 'ai', 'web', 'blockchain', 'data', 'hackathon'];
    const hasTechInterest = interests.some((i: string) => 
      techInterests.some(tech => i.toLowerCase().includes(tech))
    );
    const isHackathon = oppText.includes('hackathon') || oppText.includes('devpost') || 
                         oppText.includes('mlh') || oppText.includes('dorahacks');
    
    if (hasTechInterest && isHackathon) {
      score = Math.max(score, 0.7); // Tech students get minimum 70% for hackathons
    }

    // Bonus for major match
    const major = (profile.major || '').toLowerCase();
    if (major && oppText.includes(major)) {
      score = Math.min(score + 0.2, 1.0);
    }

    // Bonus for CS/Software students on technical opportunities
    if (major.includes('computer') || major.includes('software') || major.includes('engineering')) {
      if (isHackathon || oppText.includes('tech') || oppText.includes('code')) {
        score = Math.min(score + 0.15, 1.0);
      }
    }

    return score;
  }

  private scoreLocation(opp: Scholarship, profile: any): number {
    const userCountry = (profile.country || '').toLowerCase();
    const userState = (profile.state || '').toLowerCase();

    // If no location data, neutral score
    if (!userCountry && !userState) return 0.5;

    const oppStates = (opp.eligibility?.states || []).map((s: string) => s.toLowerCase());
    const oppCitizenship = (opp.eligibility?.citizenship || '').toLowerCase();
    const oppTags = (opp.tags || []).map(t => t.toLowerCase());

    // 1. Local Match (State/City) - Highest Priority
    if (userState && oppStates.some(s => s.includes(userState))) {
      return 1.0;
    }

    // 2. National Match
    if (userCountry) {
      // Explicit citizenship match
      if (oppCitizenship && oppCitizenship.includes(userCountry)) {
        return 0.9;
      }
      // Implicit match (no restrictions or 'US' tag for US students)
      if ((!oppCitizenship || oppCitizenship === 'any') &&
        (userCountry === 'united states' || userCountry === 'us')) {
        return 0.8;
      }
    }

    // 3. International / Global
    if (oppCitizenship.includes('international') || oppTags.includes('international')) {
      return 0.7;
    }

    return 0.5; // Default neutral
  }

  private scoreUrgency(opp: Scholarship, profile: any): number {
    const daysUntil = this.getDaysUntilDeadline(opp.deadline);
    const motivation = profile.motivation || [];

    // User needs urgent funding
    if (motivation.includes('Urgent Funding')) {
      if (daysUntil <= 7) return 1.0;
      if (daysUntil <= 30) return 0.7;
      return 0.3;
    }

    // User planning ahead
    if (motivation.includes('Long-term Planning')) {
      if (daysUntil > 60) return 1.0;
      if (daysUntil > 30) return 0.7;
      return 0.4;
    }

    // Default: prefer not-too-urgent, not-too-far
    if (daysUntil >= 7 && daysUntil <= 60) {
      return 0.8;
    }
    return 0.5;
  }

  private scoreValue(opp: Scholarship, profile: any): number {
    const financialNeed = profile.financialNeed || profile.financial_need || 0;
    if (!financialNeed) return 0.5;

    const valueRatio = Math.min(opp.amount / financialNeed, 1.0);

    // Prefer opportunities that cover significant portion of need
    if (valueRatio >= 0.8) return 1.0;
    if (valueRatio >= 0.5) return 0.8;
    if (valueRatio >= 0.2) return 0.6;
    return 0.4;
  }

  private scoreEffort(opp: Scholarship, profile: any): number {
    const estimatedHours = this.estimateEffort(opp);
    const timeCommitment = profile.timeCommitment || profile.time_commitment || 'Flexible';

    // Map time commitments
    if (typeof timeCommitment === 'string' && timeCommitment.includes('few hours')) {
      if (estimatedHours <= 5) return 1.0;
      if (estimatedHours <= 10) return 0.6;
      return 0.3;
    }

    if (typeof timeCommitment === 'string' && timeCommitment.includes('Weekends')) {
      if (estimatedHours >= 10 && estimatedHours <= 48) return 1.0;
      return 0.5;
    }

    // Flexible/ongoing
    return 0.8; // Neutral
  }

  private estimateEffort(opp: Scholarship): number {
    let hours = 2; // Base application time

    // Check tags for complexity indicators
    const tags = (opp.tags || []).map(t => t.toLowerCase());

    if (tags.some(t => ['essay', 'statement'].includes(t))) {
      hours += 3; // Essay takes time
    }

    if (tags.some(t => ['recommendation', 'letter'].includes(t))) {
      hours += 1;
    }

    if (tags.some(t => ['transcript', 'documents'].includes(t))) {
      hours += 0.5;
    }

    return hours;
  }

  private generateExplanation(breakdown: MatchScoreBreakdown, opp: Scholarship, profile: any): string {
    const reasons: string[] = [];

    if (breakdown.location > 10) {
      reasons.push('Great location match');
    }
    if (breakdown.interests > 12) {
      reasons.push('Aligns with interests');
    }
    if (breakdown.urgency > 10) {
      reasons.push('Fits your timeline');
    }
    if (breakdown.value > 8) {
      reasons.push('High value');
    }
    if (breakdown.effort > 7) {
      reasons.push('Feasible workload');
    }

    if (reasons.length === 0) {
      return 'General match based on your profile';
    }

    return reasons.slice(0, 3).join(' • ');
  }

  /**
   * Rank and filter opportunities by match score
   * Adds match_tier and priority_level based on calculated scores
   */
  rankOpportunities(opportunities: Scholarship[], profile: UserProfile): Scholarship[] {
    const scored = opportunities.map(opp => {
      const matchData = this.calculateMatchScore(opp, profile);
      const matchScore = matchData.total;

      // Determine match tier based on score
      let matchTier: 'excellent' | 'good' | 'potential' | 'low';
      if (matchScore >= 85) matchTier = 'excellent';
      else if (matchScore >= 70) matchTier = 'good';
      else if (matchScore >= 50) matchTier = 'potential';
      else matchTier = 'low';

      // Determine priority based on deadline urgency + match score
      const daysUntil = this.getDaysUntilDeadline(opp.deadline);
      let priorityLevel: 'urgent' | 'high' | 'medium' | 'low';
      if (daysUntil <= 7 && matchScore >= 60) priorityLevel = 'urgent';
      else if (daysUntil <= 14 || matchScore >= 80) priorityLevel = 'high';
      else if (daysUntil <= 30 || matchScore >= 60) priorityLevel = 'medium';
      else priorityLevel = 'low';

      return {
        ...opp,
        match_score: matchScore,
        match_tier: matchTier,
        priority_level: priorityLevel,
        match_explanation: matchData.explanation
      };
    });

    // Filter out very poor matches (< 30%) and expired (score 0)
    const filtered = scored.filter(opp => opp.match_score >= 30);

    // Sort by match score descending, then by deadline ascending
    return filtered.sort((a, b) => {
      if (b.match_score !== a.match_score) return b.match_score - a.match_score;
      return this.getDaysUntilDeadline(a.deadline) - this.getDaysUntilDeadline(b.deadline);
    });
  }
}

export const matchingEngine = new OpportunityMatchingEngine();
