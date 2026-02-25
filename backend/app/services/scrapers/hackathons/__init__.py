# Init file for hackathons scrapers package
from .devpost_api_scraper import scrape_devpost_api, populate_database_with_devpost
from .mlh_scraper import scrape_mlh_events, populate_database_with_mlh
from .taikai_scraper import scrape_taikai_events, populate_database_with_taikai
from .hackquest_scraper import scrape_hackquest_events, populate_database_with_hackquest
from .unstop_scraper import populate_database_with_unstop
from .devpost_deep_scraper import populate_database_with_devpost_deep

__all__ = [
    'scrape_devpost_api',
    'populate_database_with_devpost',
    'scrape_mlh_events',
    'populate_database_with_mlh',
    'scrape_taikai_events',
    'populate_database_with_taikai',
    'scrape_hackquest_events',
    'populate_database_with_hackquest',
    'populate_database_with_unstop',
    'populate_database_with_devpost_deep',
]
