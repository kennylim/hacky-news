"""
News classification service for categorizing Hacker News stories.

Uses a two-tiered approach:
1. Pattern matching for common keywords and patterns
2. Zero-shot classification for more ambiguous titles
"""
import logging
import time
import requests
import torch
from transformers import pipeline

from app.config.settings import HN_TOP_STORIES_URL, HN_ITEM_URL, DEFAULT_FETCH_LIMIT
from app.models.database import insert_or_update_story

logger = logging.getLogger(__name__)

def fetch_latest_story_ids():
    """Fetch the latest story IDs from Hacker News API."""
    try:
        response = requests.get(HN_TOP_STORIES_URL)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch story IDs. Status code: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching latest story IDs: {str(e)}")
        return []

def fetch_story(story_id):
    """Fetch story details from Hacker News API."""
    try:
        response = requests.get(HN_ITEM_URL.format(story_id))
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch story {story_id}. Status code: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error fetching story {story_id}: {str(e)}")
        return None

def classify_news(title):
    """
    Classify Hacker News articles into appropriate categories.
    
    Uses a combination of keyword detection and transformer-based 
    zero-shot classification for accurate categorization.
    """
    if not title:
        return "Uncategorized"
        
    # Lower case the title for easier pattern matching
    title_lower = title.lower()
    
    # First attempt quick keyword-based classification for common HN patterns
    if title_lower.startswith('show hn:') or title_lower.startswith('show hn '):
        return 'Show HN'
    elif title_lower.startswith('ask hn:') or title_lower.startswith('ask hn '):
        return 'Ask HN'
    elif title_lower.startswith('tell hn:') or title_lower.startswith('tell hn '):
        return 'Ask HN'
    elif any(term in title_lower for term in ['hiring', 'job', 'career', 'salary', 'interview', 'remote work']):
        return 'Jobs & Careers'
    
    # Specialized tech patterns with more specific keywords for higher accuracy
    if any(term in title_lower for term in ['ai', 'machine learning', 'deep learning', 'neural net', 
                                         'llm', 'gpt', 'openai', 'chatgpt', 'stable diffusion', 
                                         'artificial intelligence', 'language model']):
        return 'AI & ML'
    elif any(term in title_lower for term in ['startup', 'funding', 'vc', 'venture', 'acquisition', 'ipo', 
                                           'series a', 'series b', 'angel investor', 'founder']):
        return 'Startups' 
    elif any(term in title_lower for term in ['security', 'privacy', 'hack', 'vulnerability', 'breach', 
                                           'exploit', 'cyber', 'encryption', 'authentication', 'infosec']):
        return 'Security'
    elif any(term in title_lower.split() for term in ['programming', 'code', 'coding', 'developer', 'javascript', 
                                                   'python', 'rust', 'golang', 'typescript', 'java', 'c++', 
                                                   'compiler', 'algorithm']):
        return 'Programming'
    elif any(term in title_lower for term in ['devops', 'kubernetes', 'docker', 'aws', 'cloud', 'serverless',
                                           'microservice', 'infrastructure', 'cicd', 'ci/cd']):
        return 'DevOps'
    elif any(term in title_lower for term in ['database', 'sql', 'nosql', 'data science', 'analytics',
                                           'big data', 'data engineering', 'etl', 'pandas', 'jupyter']):
        return 'Data'
    elif any(term in title_lower for term in ['chip', 'semiconductor', 'hardware', 'laptop', 'raspberry pi', 'arduino',
                                           'microcontroller', 'processor', 'circuit', 'robotics']):
        return 'Hardware'
    # Check for company names that are frequently on HN
    if any(company in title_lower for company in ['google', 'microsoft', 'apple', 'amazon', 'meta', 'facebook',
                                               'twitter', 'x.com', 'netflix', 'tesla', 'uber', 'github']):
        return 'Tech Companies'
    
    try:
        # For everything else, use zero-shot classification with tech-focused categories
        device = 0 if torch.cuda.is_available() else -1
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=device)
        candidate_labels = [
            "Programming", 
            "AI & ML",
            "Startups", 
            "Security",
            "Hardware",
            "Science & Research", 
            "Business"
        ]
        
        result = classifier(title, candidate_labels)
        return result["labels"][0] if result else "Tech"
    except Exception as e:
        logger.error(f"Error during zero-shot classification: {str(e)}")
        return "Uncategorized"

def sync_news(limit=DEFAULT_FETCH_LIMIT):
    """
    Fetch and store latest Hacker News stories.
    
    Args:
        limit: Maximum number of stories to fetch
        
    Returns:
        int: Number of stories processed
    """
    logger.info(f"Starting news sync, fetching up to {limit} stories...")
    story_ids = fetch_latest_story_ids()
    count = 0
    processed = 0
    
    for story_id in story_ids[:limit]:
        try:
            story = fetch_story(story_id)
            if story and "title" in story:
                category = classify_news(story["title"])
                if insert_or_update_story(story, category):
                    count += 1
                processed += 1
                
            # Prevent API rate limiting but don't wait too long
            if processed % 10 == 0:
                time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Error processing story {story_id}: {str(e)}")
    
    logger.info(f"Sync complete. Processed {processed} stories, successfully added/updated {count}.")
    return count