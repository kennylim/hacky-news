"""
Application configuration settings.
"""
import os

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database settings
DB_FILE = os.path.join(BASE_DIR, "hackernews.duckdb")

# API settings
HN_TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/newstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

# Server settings
DEBUG = True
PORT = 5001
HOST = "0.0.0.0"

# Classification categories
CATEGORIES = [
    "Programming",
    "AI & ML",
    "Web Development",
    "Startups",
    "Security",
    "DevOps",
    "Mobile Dev",
    "Design & UX",
    "Data",
    "Science & Research",
    "Crypto & Web3",
    "Tech Companies",
    "Hardware",
    "Jobs & Careers",
    "Show HN",
    "Ask HN"
]

# Default fetch limit
DEFAULT_FETCH_LIMIT = 50
DEFAULT_DISPLAY_LIMIT = 30