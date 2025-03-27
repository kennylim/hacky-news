"""
Database module for DuckDB operations.
"""
import logging
import duckdb
from app.config.settings import DB_FILE

logger = logging.getLogger(__name__)

def get_connection():
    """Get a DuckDB connection."""
    try:
        return duckdb.connect(DB_FILE)
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def setup_db():
    """Initialize the DuckDB database and ensure the schema is correct."""
    try:
        conn = get_connection()
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
                type TEXT,
                category TEXT DEFAULT 'Uncategorized'
            )
            """
        )
        conn.close()
        logger.info("Database setup complete.")
        return True
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        return False

def execute_query(query, params=None):
    """Execute a query and return the results."""
    try:
        conn = get_connection()
        if params:
            result = conn.execute(query, params).fetchall()
        else:
            result = conn.execute(query).fetchall()
        conn.close()
        return result
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise

def execute_and_commit(query, params=None):
    """Execute a query that modifies the database."""
    try:
        conn = get_connection()
        if params:
            conn.execute(query, params)
        else:
            conn.execute(query)
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error executing and committing query: {str(e)}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise

def insert_or_update_story(story, category):
    """Insert a new story or update an existing one."""
    if not story.get("title"):
        return False  # Skip stories without titles
    
    try:
        # Check if story exists
        conn = get_connection()
        exists = conn.execute(
            "SELECT COUNT(*) FROM hackernews WHERE id = ?", 
            [story["id"]]
        ).fetchone()[0] > 0
        
        if exists:
            query = """
                UPDATE hackernews 
                SET title = ?, url = ?, by = ?, time = ?, score = ?,
                descendants = ?, type = ?, category = ? 
                WHERE id = ?
            """
            params = [
                story.get("title"), story.get("url"), story.get("by"), 
                story.get("time"), story.get("score"), story.get("descendants"),
                story.get("type"), category, story["id"]
            ]
        else:
            query = """
                INSERT INTO hackernews 
                (id, title, url, by, time, score, descendants, type, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = [
                story["id"], story.get("title"), story.get("url"), 
                story.get("by"), story.get("time"), story.get("score"),
                story.get("descendants"), story.get("type"), category
            ]
        
        conn.execute(query, params)
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error inserting/updating story {story.get('id')}: {str(e)}")
        return False

def get_stories(category=None, limit=30):
    """Get stories, optionally filtered by category."""
    try:
        if category and category.lower() != 'all':
            query = """
                SELECT id, title, url, by, time, score, category 
                FROM hackernews 
                WHERE LOWER(category) = LOWER(?) 
                ORDER BY time DESC 
                LIMIT ?
            """
            return execute_query(query, [category, limit])
        else:
            query = """
                SELECT id, title, url, by, time, score, category 
                FROM hackernews 
                ORDER BY time DESC 
                LIMIT ?
            """
            return execute_query(query, [limit])
    except Exception as e:
        logger.error(f"Error getting stories: {str(e)}")
        return []

def search_stories(search_term, category=None, limit=50):
    """Search for stories by keyword, optionally filtered by category."""
    try:
        search_param = f"%{search_term}%"
        
        if category and category.lower() != 'all':
            query = """
                SELECT id, title, url, by, time, score, category 
                FROM hackernews 
                WHERE (title ILIKE ? OR url ILIKE ? OR by ILIKE ?) AND LOWER(category) = LOWER(?)
                ORDER BY time DESC 
                LIMIT ?
            """
            return execute_query(query, [search_param, search_param, search_param, category, limit])
        else:
            query = """
                SELECT id, title, url, by, time, score, category 
                FROM hackernews 
                WHERE title ILIKE ? OR url ILIKE ? OR by ILIKE ?
                ORDER BY time DESC 
                LIMIT ?
            """
            return execute_query(query, [search_param, search_param, search_param, limit])
    except Exception as e:
        logger.error(f"Error searching stories: {str(e)}")
        return []

def get_categories():
    """Get all available categories and their counts."""
    try:
        query = """
            SELECT category, COUNT(*) as count
            FROM hackernews
            GROUP BY category
            ORDER BY count DESC
        """
        return execute_query(query)
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        return []

def get_stats():
    """Get basic stats about the database."""
    try:
        total = execute_query("SELECT COUNT(*) FROM hackernews")[0][0]
        categories = execute_query("""
            SELECT category, COUNT(*) as count
            FROM hackernews
            GROUP BY category
            ORDER BY count DESC
        """)
        return {
            "total_stories": total,
            "categories": [
                {"name": cat[0] if cat[0] else "Uncategorized", "count": cat[1]}
                for cat in categories
            ]
        }
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return {"total_stories": 0, "categories": []}

def get_top_stories(timeframe="recent", limit=15):
    """Get top stories by points."""
    try:
        if timeframe == "recent":
            query = """
                SELECT id, title, url, by, score, time, category
                FROM hackernews
                WHERE score IS NOT NULL AND score > 10
                ORDER BY time DESC, score DESC
                LIMIT ?
            """
        else:  # all-time
            query = """
                SELECT id, title, url, by, score, time, category
                FROM hackernews
                WHERE score IS NOT NULL
                ORDER BY score DESC
                LIMIT ?
            """
        return execute_query(query, [limit])
    except Exception as e:
        logger.error(f"Error getting top stories: {str(e)}")
        return []

def get_autocomplete_suggestions(prefix, limit=7):
    """Get title suggestions for autocomplete."""
    try:
        if not prefix.strip():
            return []
            
        search_param = f"{prefix}%"
        query = """
            SELECT DISTINCT title
            FROM hackernews
            WHERE title ILIKE ?
            ORDER BY time DESC
            LIMIT ?
        """
        return execute_query(query, [search_param, limit])
    except Exception as e:
        logger.error(f"Error getting autocomplete suggestions: {str(e)}")
        return []

def ensure_test_data():
    """Ensure test data is available in the database."""
    try:
        conn = get_connection()
        
        # Check if we have data
        count = conn.execute("SELECT COUNT(*) FROM hackernews").fetchone()[0]
        
        # If no data, insert some test data
        if count == 0:
            logger.info("No data found. Inserting test data...")
            import time
            
            test_data = [
                (1, "Test Article 1", "http://example.com/1", "testuser1", int(time.time()), 100, 5, "story", "Programming"),
                (2, "Test Article 2", "http://example.com/2", "testuser2", int(time.time()) - 3600, 50, 3, "story", "AI & ML"),
                (3, "Test Article 3", "http://example.com/3", "testuser3", int(time.time()) - 7200, 75, 8, "story", "Web Development")
            ]
            
            conn.execute("""
                INSERT INTO hackernews (id, title, url, by, time, score, descendants, type, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, test_data)
            logger.info("Test data inserted successfully")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error ensuring test data: {str(e)}")
        return False