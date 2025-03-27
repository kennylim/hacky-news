"""
Hacky News Server - Main entry point for the application
"""
import logging
import time
import threading
import schedule
from app import create_app
from app.config.settings import DEBUG, PORT, HOST
from app.services.classifier import sync_news

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def refresh_news():
    """Refresh and update 100 newest Hacker News stories"""
    logger.info("Refreshing and updating 100 newest Hacker News stories")
    try:
        stories_updated = sync_news(limit=100)
        logger.info(f"Successfully updated {stories_updated} Hacker News stories")
        return stories_updated
    except Exception as e:
        logger.error(f"Error updating Hacker News stories: {str(e)}")
        return 0

def run_scheduler():
    """Run the scheduler to refresh news every 15 minutes"""
    schedule.every(15).minutes.do(refresh_news)
    logger.info("News update scheduler started, will refresh every 15 minutes")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Create the Flask application
    app = create_app()
    logger.info("Hacky News server created")
    
    # Start the news refresh in a background thread
    news_thread = threading.Thread(target=refresh_news, name="initial-news-refresh")
    news_thread.daemon = True
    news_thread.start()
    logger.info("Started initial news refresh in background")
    
    # Start the scheduler in a background thread
    scheduler_thread = threading.Thread(target=run_scheduler, name="news-scheduler")
    scheduler_thread.daemon = True
    scheduler_thread.start()
    logger.info("Started news refresh scheduler in background")
    
    # Run the Flask application (this will block until the server is stopped)
    logger.info(f"Starting Hacky News server on {HOST}:{PORT}")
    app.run(debug=DEBUG, port=PORT, host=HOST)

