from flask import Flask, jsonify, request, send_from_directory, render_template
import duckdb
from flask_cors import CORS
import os
import logging
import time
import sys
import classifier  # Import the classifier module

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static',
            template_folder='templates')
            
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

DB_FILE = "hackernews.duckdb"

@app.route("/", methods=["GET"])
def index():
    """Serve the index.html file"""
    return render_template('index.html')
    
@app.route("/debug", methods=["GET"])
def debug():
    """Debug page that shows raw database content"""
    try:
        conn = duckdb.connect(DB_FILE)
        
        # Check if table exists
        table_exists = conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='hackernews'").fetchone()[0]
        if not table_exists:
            return "Table 'hackernews' does not exist!"
            
        # Get record count
        count = conn.execute("SELECT COUNT(*) FROM hackernews").fetchone()[0]
        
        # Get the latest 10 records
        result = conn.execute("SELECT * FROM hackernews ORDER BY time DESC LIMIT 10").fetchall()
        conn.close()
        
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

@app.route("/<path:path>", methods=["GET"])
def static_files(path):
    """Serve static files"""
    logger.debug(f"Serving static file: {path}")
    return send_from_directory(app.static_folder, path)

@app.route("/news", methods=["GET"])
def get_news():
    """Fetch latest 30 stories from DuckDB"""
    try:
        category = request.args.get('category', None)
        logger.debug(f"Getting news with category filter: {category}")
        
        # Log headers for debugging CORS issues
        logger.debug(f"Request headers: {dict(request.headers)}")
        
        conn = duckdb.connect(DB_FILE)
        
        # First check if the table exists and has data
        table_check = conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='hackernews'").fetchone()
        if table_check[0] == 0:
            logger.error("Table 'hackernews' does not exist!")
            conn.close()
            return jsonify({"error": "Database table not found"}), 500
            
        # Check record count
        count = conn.execute("SELECT COUNT(*) FROM hackernews").fetchone()
        logger.debug(f"Total records in hackernews table: {count[0]}")
        
        if category and category.lower() != 'all':
            query = """
                SELECT id, title, url, by, time, score, category 
                FROM hackernews 
                WHERE category = ? 
                ORDER BY time DESC 
                LIMIT 30
            """
            result = conn.execute(query, [category]).fetchall()
        else:
            query = """
                SELECT id, title, url, by, time, score, category 
                FROM hackernews 
                ORDER BY time DESC 
                LIMIT 30
            """
            result = conn.execute(query).fetchall()
        
        conn.close()

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

@app.route("/categories", methods=["GET"])
def get_categories():
    """Get all available categories and their counts"""
    try:
        logger.debug("Getting categories")
        conn = duckdb.connect(DB_FILE)
        query = """
            SELECT category, COUNT(*) as count
            FROM hackernews
            GROUP BY category
            ORDER BY count DESC
        """
        result = conn.execute(query).fetchall()
        conn.close()

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

@app.route("/stats", methods=["GET"])
def get_stats():
    """Get basic stats about the database"""
    try:
        logger.debug("Getting stats")
        conn = duckdb.connect(DB_FILE)
        
        # Total stories
        total_query = "SELECT COUNT(*) FROM hackernews"
        total = conn.execute(total_query).fetchone()[0]
        
        # Stories per category
        category_query = """
            SELECT category, COUNT(*) as count
            FROM hackernews
            GROUP BY category
            ORDER BY count DESC
        """
        categories = conn.execute(category_query).fetchall()
        
        conn.close()

        stats = {
            "total_stories": total,
            "categories": [
                {"name": cat[0] if cat[0] else "Uncategorized", "count": cat[1]}
                for cat in categories
            ]
        }
        
        logger.debug("Returning stats")
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error in get_stats: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
@app.route("/stats/top-recent", methods=["GET"])
def get_top_recent():
    """Get top stories by points, sorted by most recent date"""
    try:
        logger.debug("Getting top recent stories")
        conn = duckdb.connect(DB_FILE)
        
        # Recent high score stories
        query = """
            SELECT id, title, url, by, score, time, category
            FROM hackernews
            WHERE score IS NOT NULL AND score > 10
            ORDER BY time DESC, score DESC
            LIMIT 15
        """
        stories = conn.execute(query).fetchall()
        
        conn.close()

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
        
@app.route("/stats/top-alltime", methods=["GET"])
def get_top_alltime():
    """Get top stories by points of all time"""
    try:
        logger.debug("Getting all-time top stories")
        conn = duckdb.connect(DB_FILE)
        
        # All-time high score stories
        query = """
            SELECT id, title, url, by, score, time, category
            FROM hackernews
            WHERE score IS NOT NULL
            ORDER BY score DESC
            LIMIT 15
        """
        stories = conn.execute(query).fetchall()
        
        conn.close()

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

@app.route("/update", methods=["GET"])
def update_news():
    """Update news data from Hacker News API"""
    try:
        # Check if we need to setup the DB
        if not os.path.exists(DB_FILE):
            classifier.setup_db()
            
        # Synchronize news
        news_count = classifier.sync_news()
        
        return jsonify({
            "status": "success", 
            "message": f"Successfully updated news data. Processed {news_count} stories."
        })
    except Exception as e:
        logger.error(f"Error updating news: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
        
@app.route("/test-data", methods=["GET"])
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

@app.route("/search", methods=["GET"])
def search_news():
    """Search for stories by keyword"""
    try:
        search_term = request.args.get('q', '')
        category = request.args.get('category', None)
        logger.debug(f"Searching for: '{search_term}' in category: {category}")
        
        if not search_term.strip():
            return jsonify({"error": "Search query is required"}), 400
        
        conn = duckdb.connect(DB_FILE)
        
        # First check if the table exists and has data
        table_check = conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='hackernews'").fetchone()
        if table_check[0] == 0:
            logger.error("Table 'hackernews' does not exist!")
            conn.close()
            return jsonify({"error": "Database table not found"}), 500
        
        # Search logic with category filter if provided
        if category and category.lower() != 'all':
            sql_query = """
                SELECT id, title, url, by, time, score, category 
                FROM hackernews 
                WHERE (title ILIKE ? OR url ILIKE ? OR by ILIKE ?) AND category = ?
                ORDER BY time DESC 
                LIMIT 50
            """
            search_param = f"%{search_term}%"
            result = conn.execute(sql_query, [search_param, search_param, search_param, category]).fetchall()
        else:
            sql_query = """
                SELECT id, title, url, by, time, score, category 
                FROM hackernews 
                WHERE title ILIKE ? OR url ILIKE ? OR by ILIKE ?
                ORDER BY time DESC 
                LIMIT 50
            """
            search_param = f"%{search_term}%"
            result = conn.execute(sql_query, [search_param, search_param, search_param]).fetchall()
        
        conn.close()
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

@app.route("/autocomplete", methods=["GET"])
def get_autocomplete_suggestions():
    """Get autocomplete suggestions based on title prefix"""
    try:
        prefix = request.args.get('q', '')
        limit = int(request.args.get('limit', 7))  # Default to 7 suggestions
        logger.debug(f"Getting autocomplete suggestions for: '{prefix}'")
        
        if not prefix.strip():
            return jsonify([])
        
        conn = duckdb.connect(DB_FILE)
        
        # Get suggestions from titles
        sql_query = """
            SELECT DISTINCT title
            FROM hackernews
            WHERE title ILIKE ?
            ORDER BY time DESC
            LIMIT ?
        """
        search_param = f"{prefix}%"
        result = conn.execute(sql_query, [search_param, limit]).fetchall()
        
        # If we don't have enough results with exact prefix, try broader match
        if len(result) < limit:
            remaining = limit - len(result)
            broader_query = """
                SELECT DISTINCT title
                FROM hackernews
                WHERE title ILIKE ? AND title NOT ILIKE ?
                ORDER BY time DESC
                LIMIT ?
            """
            broader_param = f"%{prefix}%"
            broader_result = conn.execute(broader_query, [broader_param, search_param, remaining]).fetchall()
            result.extend(broader_result)
        
        conn.close()
        
        # Format the results as an array of suggestion objects
        suggestions = [{"value": row[0]} for row in result]
        
        logger.debug(f"Returning {len(suggestions)} autocomplete suggestions")
        return jsonify(suggestions)
    except Exception as e:
        logger.error(f"Error in get_autocomplete_suggestions: {str(e)}")
        return jsonify([]), 500

@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

def ensure_test_data():
    """Ensure we have some test data in the database"""
    try:
        conn = duckdb.connect(DB_FILE)
        
        # Check if table exists
        table_exists = conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='hackernews'").fetchone()[0]
        if not table_exists:
            logger.info("Creating hackernews table")
            classifier.setup_db()
        
        # Check if we have data
        count = conn.execute("SELECT COUNT(*) FROM hackernews").fetchone()[0]
        logger.info(f"Found {count} rows in hackernews table")
        
        # If no data, insert some test data
        if count == 0:
            logger.info("No data found. Inserting test data...")
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

if __name__ == "__main__":
    logger.info("Starting Flask server...")
    
    # Check if database exists, if not create it
    if not os.path.exists(DB_FILE):
        logger.info("Database does not exist. Setting up...")
        classifier.setup_db()
        logger.info("Initial database setup complete.")
    
    # Ensure we have test data
    ensure_test_data()
    
    # Start the server
    app.run(debug=True, port=5001, host="0.0.0.0")

