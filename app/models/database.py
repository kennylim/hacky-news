"""
Database module for DuckDB operations.
"""
import logging
import contextlib
import duckdb
from app.config.settings import DB_FILE

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def db_connection():
    """
    Context manager for DuckDB connections.
    
    Usage:
        with db_connection() as conn:
            result = conn.execute("SELECT * FROM hackernews").fetchall()
    
    Returns:
        DuckDB connection object
    
    Raises:
        Exception: If connection fails
    """
    conn = None
    try:
        conn = duckdb.connect(DB_FILE)
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()


def get_connection():
    """
    Get a DuckDB connection. 
    
    Note: Consider using the db_connection context manager instead.
    
    Returns:
        DuckDB connection object
    """
    try:
        return duckdb.connect(DB_FILE)
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise


def setup_db():
    """
    Initialize the DuckDB database and ensure the schema is correct.
    
    Returns:
        bool: True if setup was successful, False otherwise
    """
    try:
        with db_connection() as conn:
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
        logger.info("Database setup complete.")
        return True
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        return False


def execute_query(query, params=None):
    """
    Execute a query and return the results.
    
    Args:
        query (str): SQL query to execute
        params (list, optional): Parameters for the query
        
    Returns:
        list: Query results
        
    Raises:
        Exception: If query execution fails
    """
    try:
        with db_connection() as conn:
            if params:
                result = conn.execute(query, params).fetchall()
            else:
                result = conn.execute(query).fetchall()
            return result
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise


def execute_and_commit(query, params=None):
    """
    Execute a query that modifies the database.
    
    Args:
        query (str): SQL query to execute
        params (list, optional): Parameters for the query
        
    Returns:
        bool: True if successful
        
    Raises:
        Exception: If query execution fails
    """
    try:
        with db_connection() as conn:
            if params:
                conn.execute(query, params)
            else:
                conn.execute(query)
            return True
    except Exception as e:
        logger.error(f"Error executing and committing query: {str(e)}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise


def insert_or_update_story(story, category):
    """
    Insert a new story or update an existing one.
    
    Args:
        story (dict): Story data dictionary
        category (str): Category to assign to the story
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not story.get("title"):
        return False  # Skip stories without titles
    
    try:
        with db_connection() as conn:
            # Check if story exists
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
            return True
    except Exception as e:
        logger.error(f"Error inserting/updating story {story.get('id')}: {str(e)}")
        return False


def get_stories(category=None, limit=30):
    """
    Get stories, optionally filtered by category.
    
    Args:
        category (str, optional): Category to filter by
        limit (int, optional): Maximum number of stories to return
        
    Returns:
        list: List of story records
    """
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
    """
    Search for stories by keyword, optionally filtered by category.
    
    Args:
        search_term (str): Term to search for
        category (str, optional): Category to filter by
        limit (int, optional): Maximum number of stories to return
        
    Returns:
        list: List of matching story records
    """
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
    """
    Get all available categories and their counts.
    
    Returns:
        list: List of tuples containing (category_name, story_count)
    """
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
    """
    Get basic stats about the database.
    
    Returns:
        dict: Dictionary containing total_stories count and categories list
    """
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
    """
    Get top stories by points.
    
    Args:
        timeframe (str): Either "recent" or "alltime"
        limit (int): Maximum number of stories to return
        
    Returns:
        list: List of top story records
    """
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
    """
    Get title suggestions for autocomplete.
    
    Args:
        prefix (str): The starting characters to match
        limit (int): Maximum number of suggestions to return
        
    Returns:
        list: List of title suggestions
    """
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
    """
    Ensure test data is available in the database.
    Only inserts test data if the database is empty.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with db_connection() as conn:
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
            
            return True
    except Exception as e:
        logger.error(f"Error ensuring test data: {str(e)}")
        return False