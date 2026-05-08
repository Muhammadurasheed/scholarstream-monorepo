# Init file for bounties scrapers package
from .multi_platform_scraper import (
    populate_database_multi_platform,
    fetch_dorahacks_hackathons,
    fetch_dorahacks_bounties,
    fetch_immunefi_bounties,
    fetch_superteam_bounties,
    fetch_gitcoin_bounties,
    scrape_all_platforms
)
from .intigriti_scraper import scrape_intigriti_programs, populate_database_with_intigriti

__all__ = [
    'populate_database_multi_platform',
    'fetch_dorahacks_hackathons',
    'fetch_dorahacks_bounties',
    'fetch_immunefi_bounties',
    'fetch_superteam_bounties',
    'fetch_gitcoin_bounties',
    'scrape_intigriti_programs',
    'populate_database_with_intigriti',
    'scrape_all_platforms'
]
