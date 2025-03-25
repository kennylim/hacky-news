# Hacky News

A modern Hacker News reader with categorization and search capabilities.

## Features

- **Categorized Stories**: View Hacker News stories organized by categories
- **Search Functionality**: Search for stories by keywords
  - **Autocomplete**: Get suggestions as you type for faster searching
- **Category Filtering**: Filter stories by category
- **Dark Mode**: Toggle between light and dark themes
- **Statistics**: View detailed stats about story distribution
- **Real-time Updates**: Fetch the latest stories from Hacker News API

## Tech Stack

- **Backend**: Python, Flask, DuckDB
- **Frontend**: HTML, CSS, JavaScript
- **AI Model**: BART-large-mnli model for story classification
- **Data Source**: Hacker News API

## Setup Instructions

1. Clone this repository:
```bash
git clone <repository-url>
cd hacker-news
```

2. Create a virtual environment and install dependencies:
```bash
# Using the provided script
./create_venv.sh
# Or manually
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Run the server:
```bash
python server.py
```

4. Access the application at http://localhost:5001

## Usage

- **Browse Categories**: Click on category pills to filter stories
- **Search**: Use the search bar to find specific stories
  - Enter keywords and press Enter or click the search icon
  - As you type, autocomplete suggestions will appear
  - Use arrow keys to navigate through suggestions or click on a suggestion
  - Press Enter to select a suggestion and search
  - Clear search results by clicking "Clear search"
- **Update Data**: Click the Update button to fetch the latest stories from Hacker News
- **View Stats**: Click the chart icon to see story statistics
- **Toggle Theme**: Switch between light and dark mode with the moon/sun icon

## Project Structure

- **server.py**: Main Flask application with API endpoints
- **classifier.py**: Story classification and database management
- **static/**: Frontend assets (CSS, JavaScript)
- **templates/**: HTML templates
- **hackernews.duckdb**: Local database file

## API Endpoints

- **GET /news**: Get the latest stories (optionally filtered by category)
- **GET /search**: Search for stories by keywords
- **GET /autocomplete**: Get autocomplete suggestions for search input
- **GET /categories**: Get all available categories
- **GET /stats**: Get statistics about the database
- **GET /stats/top-recent**: Get recent top-scored stories
- **GET /stats/top-alltime**: Get all-time top-scored stories
- **GET /update**: Update the database with fresh stories

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.
