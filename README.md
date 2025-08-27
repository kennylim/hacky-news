# Hacky News

A modern Hacker News reader with AI-powered categorization and advanced search capabilities. Built with Python, Flask, and DuckDB.

 
 <img width="1205" height="948" alt="Screenshot 2025-08-27 at 8 26 47 AM" src="https://github.com/user-attachments/assets/2495af5d-ff60-442b-b090-37c16d33638b" />
 <img width="1082" height="962" alt="Screenshot 2025-08-27 at 8 27 44 AM" src="https://github.com/user-attachments/assets/928bdfb4-83b5-48c8-88a4-62aeb5b1853d" />



## Features

- **News Classification**: Automatically classifies Hacker News stories using both keyword matching and a BART-large-mnli model
- **Search**: Full-text search with autocomplete suggestions
- **Category Filtering**: Browse stories by technology categories
- **Updates**: Fetch the latest stories from Hacker News API
- **Dark/Light Mode**: Toggle between themes for comfortable reading
- **Statistics Dashboard**: View story distribution and top posts
- **Responsive Design**: Works on desktop and mobile devices

## Architecture

```
┌───────────────────┐     ┌─────────────────────────────────────┐
│                   │     │             Flask Server            │
│   Hacker News API │     │ ┌───────────┐       ┌────────────┐  │
│                   │     │ │           │       │            │  │
│  ┌─────────────┐  │     │ │  API      │       │ AI         │  │
│  │             │  │     │ │  Routes   │◄─────►│ Classifier │  │
│  │   Stories   │  │     │ │           │       │            │  │
│  │             │  │     │ └───────────┘       └────────────┘  │
│  └─────────────┘  │     │        │                    ▲       │
│         ▲         │     │        ▼                    │       │
└─────────┼─────────┘     │ ┌───────────┐       ┌────────────┐  │
          │               │ │           │       │            │  │
          │               │ │  Database │       │Transformers│  │
          └──────────────►│ │  Module   │       │   Model    │  │
                          │ │           │       │            │  │
                          │ └───────────┘       └────────────┘  │
                          │        │                            │
                          └────────┼────────────────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │                 │
                          │  DuckDB         │
                          │  Database       │
                          │                 │
                          └─────────────────┘
                                   ▲
                                   │
                                   │
                          ┌─────────────────┐        ┌──────────────┐
                          │                 │        │              │
                          │  Web Frontend   │◄───────┤   Browser    │
                          │  (HTML/CSS/JS)  │        │              │
                          │                 │        │              │
                          └─────────────────┘        └──────────────┘
```

This architecture follows a modular design with clear separation of concerns:
1. **Data Retrieval Layer**: Fetches stories from the Hacker News API
2. **Classification Layer**: Processes stories using keyword matching and ML-based classification
3. **Data Storage Layer**: Persists classified stories in DuckDB
4. **API Layer**: Provides RESTful endpoints for the frontend
5. **Frontend Layer**: User interface built with HTML, CSS, and JavaScript

## Tech Stack

- **Backend**: Python 3.12+, Flask 2.x+, DuckDB
- **Frontend**: HTML5, CSS3, JavaScript (ES2025), Chart.js
- **Machine Learning**: Hugging Face Transformers with BART-large-mnli model
- **Data Source**: Hacker News API

## Prerequisites

- Python 3.12 or higher
- pip or Poetry/PDM for dependency management


## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/hacky-news.git
cd hacky-news

# Build and run with Docker Compose
docker-compose up
```

### Manual Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hacky-news.git
cd hacky-news
```

2. Create a virtual environment and install dependencies:
```bash
# Using Poetry (recommended)
poetry install

# Using pip
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Run the server:
```bash
python server.py
```

4. Access the application at http://localhost:5001

## Project Structure

```
hacky-news/
├── app/                    # Main application package
│   ├── __init__.py        # App factory function
│   ├── api/               # API endpoints
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── config/            # Configuration settings
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── models/            # Database models
│   │   ├── __init__.py
│   │   └── database.py
│   ├── services/          # Business logic services
│   │   ├── __init__.py
│   │   └── classifier.py
│   └── utils/             # Utility functions
│       └── __init__.py
├── static/                # Static assets
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── main.js
├── templates/             # HTML templates
│   └── index.html
├── tests/                 # Unit tests
│   ├── __init__.py
│   └── test_api.py
├── server.py              # Development server
├── wsgi.py                # Production WSGI entry point
├── classifier.py          # Legacy classifier (now refactored)
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project metadata and Poetry dependencies
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Container orchestration
├── create_venv.sh         # Script to create virtual environment
└── README.md              # Project documentation
```

## How It Works

### AI Classification System

Hacky News uses a two-tiered approach to classify Hacker News stories:
1. **Pattern Matching**: First attempts to classify using keyword detection for common patterns
2. **Zero-shot Classification**: For more ambiguous titles, uses the BART-large-mnli transformer model

Stories are classified into these categories:
- Programming
- AI & ML
- Web Development
- Startups
- Security
- DevOps
- Mobile Dev
- Design & UX
- Data
- Science & Research
- Crypto & Web3
- Tech Companies
- Hardware
- Jobs & Careers
- Show HN
- Ask HN

### API Reference

The application provides the following RESTful endpoints:

#### Get Latest Stories
```
GET /news
GET /news?category=Programming
```

#### Search Stories
```
GET /search?q=your_search_term
GET /search?q=your_search_term&category=AI+%26+ML
```

#### Get Autocomplete Suggestions
```
GET /autocomplete?q=partial_term
```

#### Get Categories
```
GET /categories
```

#### Get Statistics
```
GET /stats
GET /stats/top-recent
GET /stats/top-alltime
```

#### Update Database
```
GET /update
GET /update?limit=100
```

## Development

### Setting Up for Development

```bash
# Clone the repository
git clone https://github.com/yourusername/hacky-news.git
cd hacky-news

# Set up development environment with Poetry
poetry install --with dev

# Or with pip
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app
```

### Production Deployment

For production deployment, we recommend using Docker or Gunicorn:

#### Using Docker (Recommended)

```bash
docker build -t hacky-news .
docker run -p 5001:5001 hacky-news
```

#### Using Gunicorn

```bash
gunicorn wsgi:app -b 0.0.0.0:5001 --workers 4
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Run the tests (`pytest`)
5. Commit your changes (`git commit -am 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature-name`)
7. Create a new Pull Request

## Benefits of This Solution

- **Efficient Resource Usage**: DuckDB provides fast SQL queries with minimal resource usage
- **Intelligent Categorization**: ML-powered classification gives more accurate results than rule-based systems
- **Developer Friendly**: Simple architecture makes it easy to extend and maintain
- **Modern Stack**: Uses current best practices and frameworks
- **Low Latency**: Optimized for quick response times
- **Privacy-Focused**: Runs ML locally instead of sending data to external APIs

## Roadmap

Future enhancements planned for this project:

- Better ML models for better classification
- Integration with other news sources
- Personalization with user profiles
- Weekly email digests

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
