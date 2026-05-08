
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.personalization_engine import personalization_engine
from app.models import UserProfile

async def verify_personalization():
    print("=== PERSONALIZATION VERIFICATION PROOF ===")
    
    # 1. Mock Opportunities
    opp_hackathon = {
        "name": "Global AI Hackathon",
        "description": "Build the next generation of AI agents using Python and LLMs.",
        "tags": ["AI", "Python", "Machine Learning", "Hackathon"],
        "eligibility": {"majors": ["Computer Science"], "grade_levels": ["Undergraduate"]}
    }
    
    opp_design_contest = {
        "name": "Future of Design Award",
        "description": "Create stunning UI/UX designs for mobile apps. Use Figma.",
        "tags": ["Design", "UI/UX", "Arts", "Creative"],
        "eligibility": {"majors": ["Arts", "Design"]}
    }
    
    # 2. Mock Users
    user_coder = {
        "interests": ["AI", "Coding", "Python", "Hackathons"],
        "major": "Computer Science",
        "academic_status": "Undergraduate",
        "background": ["Software Engineering"]
    }
    
    user_designer = {
        "interests": ["Design", "Art", "UI/UX", "Sketching"],
        "major": "Arts",
        "academic_status": "Undergraduate",
        "background": ["Graphic Design"]
    }
    
    # 3. Calculate Scores
    print("\n[User A: The Coder]")
    score_coder_hack = personalization_engine.calculate_personalized_score(opp_hackathon, user_coder)
    score_coder_design = personalization_engine.calculate_personalized_score(opp_design_contest, user_coder)
    print(f"Match for AI Hackathon: {score_coder_hack:.1f}%")
    print(f"Match for Design Award: {score_coder_design:.1f}%")
    
    print("\n[User B: The Designer]")
    score_designer_hack = personalization_engine.calculate_personalized_score(opp_hackathon, user_designer)
    score_designer_design = personalization_engine.calculate_personalized_score(opp_design_contest, user_designer)
    print(f"Match for AI Hackathon: {score_designer_hack:.1f}%")
    print(f"Match for Design Award: {score_designer_design:.1f}%")
    
    # 4. Verify Differentiation
    if score_coder_hack > score_coder_design and score_designer_design > score_designer_hack:
        print("\n✅ PASSED: System correctly prioritizes relevant opportunities based on profile.")
    else:
        print("\n❌ FAILED: Scores are not distinct enough.")

if __name__ == "__main__":
    asyncio.run(verify_personalization())
