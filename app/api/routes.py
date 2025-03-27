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
    ensure_test_data
)
from app.services.classifier import sync_news
from app.config.settings import DEFAULT_DISPLAY_LIMIT

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint for API routes
api_bp = Blueprint('api', __name__)


@api_bp.route("/", methods=["GET"])
def index():
    """Serve the index.html file"""
    return render_template('index.html')


@api_bp.route("/debug", methods=["GET"])
def debug():
    """Debug page that shows raw database content"""
    try:
        from app.models.database import execute_query
        
        # Check if table exists
        table_exists = execute_query("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='hackernews'")[0][0]
        if not table_exists:
            return "Table 'hackernews' does not exist!"
            
        # Get record count
        count = execute_query("SELECT COUNT(*) FROM hackernews")[0][0]
        
        # Get the latest 10 records
        result = execute_query("SELECT * FROM hackernews ORDER BY time DESC LIMIT 10")
        
        # Format as HTML
        html = f"<h1>Debug Info</h1>"
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
        logger.debug(f"Getting news with category: {category}, limit: {limit}")
        
        # Get stories from database
        result = get_stories(category, limit)
        
        # Format response
        news_list = [
            {
                "id": row[0],
                "title": row[1],
                "url": row[2],
                "by": row[3],
                "time": row[4],
                "score": row[5],
                "category": row[6]
            }
            for row in result
        ]
        
        logger.debug(f"Returning {len(news_list)} news items")
        return jsonify(news_list)
    except Exception as e:
        logger.error(f"Error in get_news: {str(e)}")
        return jsonify({"error": str(e)}), 500


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
        
        logger.debug(f"Returning {len(categories)} categories")
        return jsonify(categories)
    except Exception as e:
        logger.error(f"Error in get_categories: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/stats", methods=["GET"])
def get_all_stats():
    """Get basic stats about the database"""
    try:
        logger.debug("Getting stats")
        stats = get_stats()
        
        logger.debug("Returning stats")
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error in get_stats: {str(e)}")
        return jsonify({"error": str(e)}), 500
        

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
        
        logger.debug(f"Returning {len(result)} recent top stories")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_top_recent: {str(e)}")
        return jsonify({"error": str(e)}), 500
        

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
        
        logger.debug(f"Returning {len(result)} all-time top stories")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in get_top_alltime: {str(e)}")
        return jsonify({"error": str(e)}), 500


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
        
        return jsonify({
            "status": "success", 
            "message": f"Successfully updated news data. Processed {news_count} stories."
        })
    except Exception as e:
        logger.error(f"Error updating news: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


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
    return jsonify(sample_data)


@api_bp.route("/search", methods=["GET"])
def search_news():
    """Search for stories by keyword"""
    try:
        search_term = request.args.get('q', '')
        category = request.args.get('category', None)
        limit = int(request.args.get('limit', 50))
        logger.debug(f"Searching for: '{search_term}' in category: {category}, limit: {limit}")
        
        if not search_term.strip():
            return jsonify({"error": "Search query is required"}), 400
        
        # Get stories from database
        result = search_stories(search_term, category, limit)
        
        # Format response
        news_list = [
            {
                "id": row[0],
                "title": row[1],
                "url": row[2],
                "by": row[3],
                "time": row[4],
                "score": row[5],
                "category": row[6]
            }
            for row in result
        ]
        
        logger.debug(f"Search returned {len(news_list)} results")
        return jsonify(news_list)
    except Exception as e:
        logger.error(f"Error in search_news: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/autocomplete", methods=["GET"])
def autocomplete():
    """Get autocomplete suggestions based on title prefix"""
    try:
        prefix = request.args.get('q', '')
        limit = int(request.args.get('limit', 7))  # Default to 7 suggestions
        logger.debug(f"Getting autocomplete suggestions for: '{prefix}'")
        
        if not prefix.strip():
            return jsonify([])
        
        # Get suggestions from database
        result = get_autocomplete_suggestions(prefix, limit)
        
        # Format the results as an array of suggestion objects
        suggestions = [{"value": row[0]} for row in result]
        
        logger.debug(f"Returning {len(suggestions)} autocomplete suggestions")
        return jsonify(suggestions)
    except Exception as e:
        logger.error(f"Error in get_autocomplete_suggestions: {str(e)}")
        return jsonify([]), 500