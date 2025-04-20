"""
API routes for the Hacky News application.
"""
import logging
import time
from flask import Blueprint, jsonify, request, render_template
from app.models.database import (
    get_stories,
    search_stories,
    get_categories,
    get_stats,
    get_top_stories,
    get_autocomplete_suggestions,
    setup_db,
    ensure_test_data,
    execute_query
)
from app.services.classifier import sync_news
from app.config.settings import DEFAULT_DISPLAY_LIMIT

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint for API routes
api_bp = Blueprint('api', __name__)


# Helper functions for standardizing API responses
def create_success_response(data, status_code=200):
    """
    Create a standardized success response.
    
    Args:
        data: The data to return
        status_code (int): HTTP status code
        
    Returns:
        tuple: (response_json, status_code)
    """
    return jsonify(data), status_code


def create_error_response(message, status_code=500):
    """
    Create a standardized error response.
    
    Args:
        message (str): Error message
        status_code (int): HTTP status code
        
    Returns:
        tuple: (response_json, status_code)
    """
    return jsonify({"error": str(message)}), status_code


def format_story(row):
    """
    Format a story database row as a JSON-friendly dictionary.
    
    Args:
        row: Database row containing story data
        
    Returns:
        dict: Formatted story data
    """
    return {
        "id": row[0],
        "title": row[1],
        "url": row[2],
        "by": row[3],
        "time": row[4],
        "score": row[5],
        "category": row[6]
    }


@api_bp.route("/", methods=["GET"])
def index():
    """Serve the index.html file"""
    return render_template('index.html')


@api_bp.route("/debug", methods=["GET"])
def debug():
    """Debug page that shows raw database content"""
    try:
        # Check if table exists
        table_exists = execute_query(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='hackernews'"
        )[0][0]
        if not table_exists:
            return "Table 'hackernews' does not exist!"
        
        # Get record count
        count = execute_query("SELECT COUNT(*) FROM hackernews")[0][0]
        
        # Get the latest 10 records
        result = execute_query("SELECT * FROM hackernews ORDER BY time DESC LIMIT 10")
        
        # Format as HTML
        html = "<h1>Debug Info</h1>"
        html += f"<p>Total records: {count}</p>"
        html += "<h2>Latest 10 Records</h2>"
        
        if result:
            html += "<table border='1'>"
            html += "<tr><th>ID</th><th>Title</th><th>Category</th><th>Score</th><th>Time</th></tr>"
            for row in result:
                html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[8]}</td><td>{row[5]}</td><td>{row[4]}</td></tr>"
            html += "</table>"
        else:
            html += "<p>No records found</p>"
        
        return html
    except Exception as e:
        return f"Error: {str(e)}"


@api_bp.route("/news", methods=["GET"])
def get_news():
    """Fetch latest stories from DuckDB"""
    try:
        category = request.args.get('category', None)
        limit = int(request.args.get('limit', DEFAULT_DISPLAY_LIMIT))
        logger.debug("Getting news with category: %s, limit: %s", category, limit)
        
        # Get stories from database
        result = get_stories(category, limit)
        
        # Format response using the helper function
        news_list = [format_story(row) for row in result]
        
        logger.debug("Returning %s news items", len(news_list))
        return create_success_response(news_list)
    except Exception as e:
        logger.error("Error in get_news: %s", str(e))
        return create_error_response(f"Failed to retrieve news: {str(e)}")


@api_bp.route("/categories", methods=["GET"])
def get_all_categories():
    """Get all available categories and their counts"""
    try:
        logger.debug("Getting categories")
        result = get_categories()
        
        # Format response
        categories = [
            {
                "name": row[0] if row[0] else "Uncategorized",
                "count": row[1]
            }
            for row in result
        ]
        
        logger.debug("Returning %s categories", len(categories))
        return create_success_response(categories)
    except Exception as e:
        logger.error("Error in get_categories: %s", str(e))
        return create_error_response(f"Failed to retrieve categories: {str(e)}")


@api_bp.route("/stats", methods=["GET"])
def get_all_stats():
    """Get basic stats about the database"""
    try:
        logger.debug("Getting stats")
        stats = get_stats()
        
        logger.debug("Returning stats")
        return create_success_response(stats)
    except Exception as e:
        logger.error("Error in get_stats: %s", str(e))
        return create_error_response(f"Failed to retrieve stats: {str(e)}")


@api_bp.route("/stats/top-recent", methods=["GET"])
def get_top_recent_stories():
    """Get top stories by points, sorted by most recent date"""
    try:
        logger.debug("Getting top recent stories")
        limit = int(request.args.get('limit', 15))
        
        # Get stories from database
        stories = get_top_stories("recent", limit)
        
        # Format response
        result = [
            {
                "id": story[0],
                "title": story[1],
                "url": story[2],
                "by": story[3],
                "score": story[4],
                "time": story[5],
                "category": story[6] if story[6] else "Uncategorized"
            }
            for story in stories
        ]
        
        logger.debug("Returning %s recent top stories", len(result))
        return create_success_response(result)
    except Exception as e:
        logger.error("Error in get_top_recent: %s", str(e))
        return create_error_response(f"Failed to retrieve top recent stories: {str(e)}")


@api_bp.route("/stats/top-alltime", methods=["GET"])
def get_top_alltime_stories():
    """Get top stories by points of all time"""
    try:
        logger.debug("Getting all-time top stories")
        limit = int(request.args.get('limit', 15))
        
        # Get stories from database
        stories = get_top_stories("alltime", limit)
        
        # Format response
        result = [
            {
                "id": story[0],
                "title": story[1],
                "url": story[2],
                "by": story[3],
                "score": story[4],
                "time": story[5],
                "category": story[6] if story[6] else "Uncategorized"
            }
            for story in stories
        ]
        
        logger.debug("Returning %s all-time top stories", len(result))
        return create_success_response(result)
    except Exception as e:
        logger.error("Error in get_top_alltime: %s", str(e))
        return create_error_response(f"Failed to retrieve top all-time stories: {str(e)}")


@api_bp.route("/update", methods=["GET"])
def update_news():
    """Update news data from Hacker News API"""
    try:
        # Ensure database is set up
        setup_db()
        
        # Get limit parameter
        limit = int(request.args.get('limit', 50))
        
        # Synchronize news
        news_count = sync_news(limit)
        
        return create_success_response({
            "status": "success", 
            "message": f"Successfully updated news data. Processed {news_count} stories."
        })
    except Exception as e:
        logger.error("Error updating news: %s", str(e))
        return create_error_response(f"Failed to update news: {str(e)}")


@api_bp.route("/test-data", methods=["GET"])
def test_data():
    """Return test data for debugging"""
    sample_data = [
        {
            "id": 1,
            "title": "Test Article 1",
            "url": "http://example.com/1",
            "by": "testuser1",
            "time": int(time.time()),
            "score": 100,
            "category": "Programming"
        },
        {
            "id": 2,
            "title": "Test Article 2",
            "url": "http://example.com/2",
            "by": "testuser2",
            "time": int(time.time()) - 3600,
            "score": 50,
            "category": "AI & ML"
        },
        {
            "id": 3,
            "title": "Test Article 3",
            "url": "http://example.com/3",
            "by": "testuser3",
            "time": int(time.time()) - 7200,
            "score": 75,
            "category": "Web Development"
        }
    ]
    logger.debug("Returning test data")
    return create_success_response(sample_data)


@api_bp.route("/search", methods=["GET"])
def search_news():
    """Search for stories by keyword"""
    try:
        search_term = request.args.get('q', '')
        category = request.args.get('category', None)
        limit = int(request.args.get('limit', 50))
        logger.debug("Searching for: '%s' in category: %s, limit: %s", search_term, category, limit)
        
        if not search_term.strip():
            return create_error_response("Search query is required", 400)
        
        # Get stories from database
        result = search_stories(search_term, category, limit)
        
        # Format response
        news_list = [format_story(row) for row in result]
        
        logger.debug("Search returned %s results", len(news_list))
        return create_success_response(news_list)
    except Exception as e:
        logger.error("Error in search_news: %s", str(e))
        return create_error_response(f"Search failed: {str(e)}")


@api_bp.route("/autocomplete", methods=["GET"])
def autocomplete():
    """Get autocomplete suggestions based on title prefix"""
    try:
        prefix = request.args.get('q', '')
        limit = int(request.args.get('limit', 7))  # Default to 7 suggestions
        logger.debug("Getting autocomplete suggestions for: '%s'", prefix)
        
        if not prefix.strip():
            return create_success_response([])
        
        # Get suggestions from database
        result = get_autocomplete_suggestions(prefix, limit)
        
        # Format the results as an array of suggestion objects
        suggestions = [{"value": row[0]} for row in result]
        
        logger.debug("Returning %s autocomplete suggestions", len(suggestions))
        return create_success_response(suggestions)
    except Exception as e:
        logger.error("Error in get_autocomplete_suggestions: %s", str(e))
        return create_error_response(f"Autocomplete failed: {str(e)}")