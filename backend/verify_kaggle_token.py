import os
import structlog
from kaggle.api.kaggle_api_extended import KaggleApi

logger = structlog.get_logger()

def verify_kaggle_auth():
    """Verify Kaggle authentication with the new token"""
    try:
        # Set env vars explicitly for this test process
        # (In production these will be loaded from .env)
        os.environ['KAGGLE_USERNAME'] = 'rasheedyekini'
        # Try mapping the new token to the standard KAGGLE_KEY variable
        os.environ['KAGGLE_KEY'] = 'KGAT_e91caf153e94c30a1dbba04024ffd2fe'
        # Also keep KAGGLE_API_TOKEN just in case
        os.environ['KAGGLE_API_TOKEN'] = 'KGAT_e91caf153e94c30a1dbba04024ffd2fe'
        
        print("Authenticating with Kaggle (using KAGGLE_KEY)...")
        api = KaggleApi()
        api.authenticate()
        print("Authentication successful!")
        
        print("Fetching competitions...")
        competitions = api.competitions_list(category="all", sort_by="prize", page=1)
        print(f"Found {len(competitions)} competitions")
        
        for comp in competitions[:3]:
            print(f"- {comp.ref}: {comp.reward}")
            
    except Exception as e:
        print(f"Authentication failed: {e}")
        # Debug info
        print("\nEnvironment variables:")
        print(f"KAGGLE_USERNAME: {os.environ.get('KAGGLE_USERNAME')}")
        print(f"KAGGLE_API_TOKEN: {os.environ.get('KAGGLE_API_TOKEN')}")

if __name__ == "__main__":
    verify_kaggle_auth()
