import requests
import duckdb
import json
import time
import os
import sys
import torch
from transformers import pipeline

HN_TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/newstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
DB_FILE = "hackernews.duckdb"

def setup_venv():
    """Set up and activate a virtual environment."""
    if not os.path.exists("venv"):
        os.system(f"{sys.executable} -m venv venv")
        print("✅ Virtual environment created.")
    else:
        print("✅ Virtual environment already exists.")

def install_dependencies():
    """Install required dependencies."""
    pip_cmd = "venv/bin/pip" if os.name != "nt" else "venv\\Scripts\\pip"
    os.system(f"{pip_cmd} install requests duckdb transformers torch")
    print("✅ Dependencies installed.")

def setup_db():
    """Initialize the DuckDB database and ensure the category column exists."""
    conn = duckdb.connect(DB_FILE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS hackernews (
            id INTEGER PRIMARY KEY,
            title TEXT,
            url TEXT,
            by TEXT,
            time INTEGER,
            score INTEGER,
            descendants INTEGER,
            type TEXT
        )
        """
    )
    # Ensure category column exists
    existing_columns = conn.execute("PRAGMA table_info(hackernews)").fetchall()
    column_names = [col[1] for col in existing_columns]
    if "category" not in column_names:
        conn.execute("ALTER TABLE hackernews ADD COLUMN category TEXT DEFAULT 'Uncategorized'")
    conn.close()
    print("✅ Database setup complete.")

def fetch_latest_story_ids():
    """Fetch the latest story IDs from Hacker News."""
    response = requests.get(HN_TOP_STORIES_URL)
    return response.json() if response.status_code == 200 else []

def fetch_story(story_id):
    """Fetch story details from Hacker News."""
    response = requests.get(HN_ITEM_URL.format(story_id))
    return response.json() if response.status_code == 200 else None

def story_exists(story_id, conn):
    """Check if a story exists in the database."""
    result = conn.execute("SELECT COUNT(*) FROM hackernews WHERE id = ?", (story_id,)).fetchone()
    return result[0] > 0

def classify_news(title):
    """
    Classify Hacker News articles with categories appropriate for the tech community.
    
    Uses a combination of keyword detection and transformer-based zero-shot classification
    to provide more accurate categorization for Hacker News content.
    """
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

def insert_or_update_story(story, conn):
    """Insert a new story if not exists, otherwise update it."""
    if not story.get("title"):
        return  # Skip stories without titles
    
    category = classify_news(story["title"])
    
    if story_exists(story["id"], conn):
        conn.execute(
            """
            UPDATE hackernews SET title = ?, url = ?, by = ?, time = ?, score = ?,
            descendants = ?, type = ?, category = ? WHERE id = ?
            """,
            (story.get("title"), story.get("url"), story.get("by"), story.get("time"), 
             story.get("score"), story.get("descendants"), story.get("type"), category, story["id"])
        )
    else:
        conn.execute(
            """
            INSERT INTO hackernews (id, title, url, by, time, score, descendants, type, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (story["id"], story.get("title"), story.get("url"), story.get("by"), story.get("time"), 
             story.get("score"), story.get("descendants"), story.get("type"), category)
        )

def sync_news():
    """Fetch and store latest Hacker News stories."""
    conn = duckdb.connect(DB_FILE)
    story_ids = fetch_latest_story_ids()
    count = 0
    
    for story_id in story_ids[:50]:
        story = fetch_story(story_id)
        if story:
            insert_or_update_story(story, conn)
            count += 1
        time.sleep(0.5)  # Prevent API rate limiting but don't wait too long
    
    conn.close()
    print(f"✅ Sync complete. Processed {count} stories.")
    return count

def display_recent_stories():
    """Fetch and display the most recent 25 stories in a readable format."""
    conn = duckdb.connect(DB_FILE)
    result = conn.execute("SELECT * FROM hackernews ORDER BY time DESC LIMIT 25").fetchall()
    conn.close()
    print("\n🔹 Latest 25 Hacker News Stories:")
    for story in result:
        print(f"📰 {story[1]}\n🔗 {story[2]}\n👤 By: {story[3]} | ⏳ Time: {story[4]} | 👍 Score: {story[5]} | 💬 Comments: {story[6]} | 🏷 Category: {story[8]}\n")

def main():
    """Main entry point for running the classifier directly."""
    print("🔹 Setting up environment...")
    setup_venv()
    install_dependencies()
    setup_db()
    sync_news()
    display_recent_stories()
    print("✅ Ready!")

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        print("⚠️ SystemExit caught. Ensure no sys.exit() is called unexpectedly.")
    except Exception as e:
        print(f"⚠️ Error: {str(e)}")

