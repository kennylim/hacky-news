/**
 * Hacky News - A modern interface for Hacker News stories
 * 
 * This JavaScript file handles the client-side functionality of Hacky News,
 * including data fetching, UI rendering, search, filtering, and analytics.
 * 
 * The code is organized into logical sections:
 * - DOM elements and state variables
 * - API helpers for data fetching
 * - Utility functions
 * - Core data loading functions
 * - UI rendering functions
 * - Event handlers
 * - Initialization
 */

// DOM elements
const refreshBtn = document.getElementById('refresh-btn');
const themeToggle = document.getElementById('theme-toggle');
const categoriesList = document.getElementById('categories-list');
const newsContent = document.getElementById('news-content');
const selectedCategory = document.getElementById('selected-category');
const updateLink = document.getElementById('update-link');
const viewStatsBtn = document.getElementById('view-stats-btn');
const statsModal = document.getElementById('stats-modal');
const modalClose = document.querySelector('.modal-close');
const tabBtns = document.querySelectorAll('.tab-btn');
const modalTotalStories = document.getElementById('modal-total-stories');
const modalAskHnCount = document.getElementById('modal-ask-hn-count');
const modalShowHnCount = document.getElementById('modal-show-hn-count');
const searchForm = document.getElementById('search-form');
const searchInput = document.getElementById('search-input');
const autocompleteContainer = document.getElementById('autocomplete-container');

// State
let currentCategory = 'all';
let darkMode = localStorage.getItem('darkMode') === 'true';
let currentSearchQuery = '';
let isSearchMode = false;
let autocompleteTimeout = null;
let selectedAutocompleteIndex = -1;

// Apply theme on page load
if (darkMode) {
    document.body.setAttribute('data-theme', 'dark');
    themeToggle.innerHTML = '<i class="bi bi-sun"></i>';
}

// Fetch data from API
async function fetchData(endpoint) {
    try {
        const response = await fetch(endpoint);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching data from ${endpoint}:`, error);
        return null;
    }
}

// Format timestamp to readable date
function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 60) {
        return `${diffMins} min${diffMins !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
        return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
        return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    }
}

// Load and render categories
async function loadCategories() {
    const categories = await fetchData('/categories');
    if (!categories) return;

    // Clear existing categories except "All"
    categoriesList.innerHTML = '<span class="category-pill active" data-category="all">All</span>';

    // Primary categories that should appear first with clean names
    const primaryCategories = [
        { key: "Programming", label: "Programming" },
        { key: "AI & ML", label: "AI & ML" },
        { key: "Web Development", label: "Web Dev" },
        { key: "Startups", label: "Startups" },
        { key: "Security", label: "Security" },
        { key: "DevOps", label: "DevOps" },
        { key: "Mobile Dev", label: "Mobile" },
        { key: "Design & UX", label: "Design" },
        { key: "Data", label: "Data" },
        { key: "Show HN", label: "Show HN" },
        { key: "Ask HN", label: "Ask HN" },
        { key: "Science & Research", label: "Science" },
        { key: "Crypto & Web3", label: "Crypto" },
        { key: "Tech Companies", label: "Tech Co." },
        { key: "Hardware", label: "Hardware" },
        { key: "Jobs & Careers", label: "Jobs" }
    ];
    
    // Organize categories
    const primaryCats = [];
    const otherCats = [];
    
    // Function to find a category by name in the categories array
    const findCategory = (name) => categories.find(c => c.name === name);
    
    // Organize primary categories first
    primaryCategories.forEach(cat => {
        const found = findCategory(cat.key);
        if (found && found.count > 0) {
            primaryCats.push({
                name: cat.key,
                label: cat.label,
                count: found.count
            });
        }
    });
    
    // Then add any remaining categories
    categories.forEach(cat => {
        // Skip if it's already in primaryCats
        if (!primaryCategories.some(pc => pc.key === cat.name) && cat.count > 0) {
            otherCats.push({
                name: cat.name,
                label: cat.name,
                count: cat.count
            });
        }
    });
    
    // Sort other categories by count
    otherCats.sort((a, b) => b.count - a.count);
    
    // Add all categories to the UI
    [...primaryCats, ...otherCats].forEach(category => {
        const pill = document.createElement('span');
        pill.className = 'category-pill';
        pill.setAttribute('data-category', category.name);
        // REMOVE COUNT: Only use the label
        pill.textContent = category.label; 
        categoriesList.appendChild(pill);
    });

    // Add event listeners
    document.querySelectorAll('.category-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            // Update UI
            document.querySelector('.category-pill.active').classList.remove('active');
            pill.classList.add('active');
            
            // Update state
            currentCategory = pill.getAttribute('data-category');
            selectedCategory.textContent = currentCategory === 'all' ? '(All)' : `(${currentCategory})`;
            
            // Load news with selected category
            loadNews(currentCategory);
        });
    });
}

// Load and render news
async function loadNews(category = 'all') {
    // Show loader
    newsContent.innerHTML = '<div class="loader"></div>';
    
    // Fetch news
    const endpoint = category !== 'all' ? `/news?category=${encodeURIComponent(category)}` : '/news';
    const news = await fetchData(endpoint);
    if (!news) {
        newsContent.innerHTML = '<p>Error loading news. Please try again.</p>';
        return;
    }
    
    // Clear loader
    newsContent.innerHTML = '';
    
    if (news.length === 0) {
        newsContent.innerHTML = '<p>No news found for this category.</p>';
        return;
    }

    // Sort news by time (newest first)
    news.sort((a, b) => b.time - a.time);
    
    // Render news items
    news.forEach(item => {
        const newsItem = document.createElement('div');
        newsItem.className = 'news-item';
        
        const domain = item.url ? new URL(item.url).hostname.replace('www.', '') : '';

        // Determine category label
        const categoryLabel = item.category || 'General'; // Default if no category

        newsItem.innerHTML = `
            <div class="news-item-header">
                <span class="news-score"><i class="bi bi-arrow-up-circle"></i> ${item.score || 0}</span>
                ${item.url ? `<span class="news-domain">${domain}</span>` : ''}
            </div>
            <h3 class="news-title"><a href="${item.url || '#'}" target="_blank" rel="noopener noreferrer">${item.title}</a></h3>
            <div class="news-meta">
                <span class="news-category">${categoryLabel}</span>
                <span class="news-author"><i class="bi bi-person"></i> ${item.by || 'Unknown'}</span>
                <span class="news-time"><i class="bi bi-clock"></i> ${formatTimestamp(item.time)}</span>
                ${item.descendants ? `<span class="news-comments"><i class="bi bi-chat-dots"></i> ${item.descendants}</span>` : ''}
            </div>
        `;
        newsContent.appendChild(newsItem);
    });
}

// Search for stories
async function searchNews(query, category = 'all') {
    // Reset state
    currentSearchQuery = query;
    isSearchMode = !!query;
    
    // Update UI
    newsContent.innerHTML = '<div class="loader"></div>';
    
    // Build endpoint
    let endpoint = `/search?q=${encodeURIComponent(query)}`;
    if (category !== 'all') {
        endpoint += `&category=${encodeURIComponent(category)}`;
    }
    
    // Fetch search results
    const results = await fetchData(endpoint);
    
    if (!results) {
        newsContent.innerHTML = '<p>Error searching news. Please try again.</p>';
        return;
    }
    
    // Clear loader
    newsContent.innerHTML = '';
    
    // Add search results info if in search mode
    if (isSearchMode) {
        const resultsInfo = document.createElement('div');
        resultsInfo.className = 'search-results-info';
        resultsInfo.innerHTML = `
            <div>Found ${results.length} results for: "${query}"</div>
            <button class="clear-search" id="clear-search">
                <i class="bi bi-x-circle"></i> Clear search
            </button>
        `;
        newsContent.appendChild(resultsInfo);
        
        // Add event listener to clear button
        document.getElementById('clear-search').addEventListener('click', clearSearch);
    }
    
    if (results.length === 0) {
        const noResults = document.createElement('p');
        noResults.textContent = `No results found for "${query}". Try a different search term.`;
        newsContent.appendChild(noResults);
        return;
    }
    
    // Render news items
    results.forEach(item => {
        const newsItem = document.createElement('div');
        newsItem.className = 'news-item';
        
        const domain = item.url ? new URL(item.url).hostname.replace('www.', '') : '';
        
        newsItem.innerHTML = `
            <div class="news-item-header">
                <div class="news-title">
                    <a href="${item.url || '#'}" target="_blank" rel="noopener noreferrer">
                        ${item.title}
                    </a>
                    ${domain ? `<small>(${domain})</small>` : ''}
                </div>
                <div class="news-score">
                    <i class="bi bi-arrow-up"></i> ${item.score || 0}
                </div>
            </div>
            <div class="news-meta">
                <span class="news-category">${item.category || 'Uncategorized'}</span>
                <span class="news-author">
                    <i class="bi bi-person"></i> ${item.by || 'Anonymous'}
                </span>
                <span class="news-time">
                    <i class="bi bi-clock"></i> ${formatTimestamp(item.time)}
                </span>
            </div>
        `;
        
        newsContent.appendChild(newsItem);
    });
}

// Clear search results and go back to normal view
function clearSearch() {
    currentSearchQuery = '';
    isSearchMode = false;
    searchInput.value = '';
    loadNews(currentCategory);
}

// Load and render stats
async function loadStats() {
    const stats = await fetchData('/stats');
    if (!stats) return;
    
    // Store stats in a global variable to reuse for modal
    window.statsData = stats;
    
    // No need to update any UI here since total stories has been moved to modal
}

// Update data from HN API
async function updateData() {
    const updateBtn = document.getElementById('update-link');
    
    // Set loading state
    updateBtn.classList.add('loading');
    updateBtn.disabled = true;
    
    // Show refresh indicator in the main content area
    const originalContent = newsContent.innerHTML;
    const notification = document.createElement('div');
    notification.className = 'update-notification';
    notification.innerHTML = '<div class="loader"></div><p>Syncing with Hacker News...</p>';
    if (newsContent.firstChild) {
        newsContent.insertBefore(notification, newsContent.firstChild);
    } else {
        newsContent.appendChild(notification);
    }
    
    try {
        const result = await fetchData('/update');
        
        if (result && result.status === 'success') {
            // Show success state
            updateBtn.classList.remove('loading');
            updateBtn.classList.add('success');
            
            // Update notification
            notification.innerHTML = `<i class="bi bi-check-circle"></i><p>${result.message}</p>`;
            notification.className = 'update-notification success';
            
            // Reload all data
            await Promise.all([
                loadCategories(),
                loadNews(currentCategory),
                loadStats()
            ]);
            
            // If stats modal is open, refresh its content too
            if (statsModal.classList.contains('show')) {
                loadDetailedStats();
            }
            
            // Reset button state after 2 seconds
            setTimeout(() => {
                updateBtn.classList.remove('success');
                updateBtn.disabled = false;
            }, 2000);
        } else {
            throw new Error('Update failed');
        }
    } catch (error) {
        // Show error state
        updateBtn.classList.remove('loading');
        updateBtn.classList.add('error');
        console.error('Error updating data:', error);
        
        // Update notification with error
        notification.innerHTML = `<i class="bi bi-exclamation-circle"></i><p>Error updating: ${error.message}</p>`;
        notification.className = 'update-notification error';
        
        // Reset button state after 2 seconds
        setTimeout(() => {
            updateBtn.classList.remove('error');
            updateBtn.disabled = false;
            
            // Remove error notification after 3 seconds
            setTimeout(() => {
                if (notification.parentNode === newsContent) {
                    newsContent.removeChild(notification);
                }
            }, 3000);
        }, 2000);
    }
}

// Create and render the categories pie chart
function renderCategoriesChart(categories) {
    const ctx = document.getElementById('categories-chart').getContext('2d');
    
    // Get total count to calculate percentages
    const totalCount = categories.reduce((sum, cat) => sum + cat.count, 0);
    
    // Prepare data for chart
    const labels = [];
    const data = [];
    const backgroundColor = [];
    
    // Set predefined colors inspired by Financial Times charting palette
    const categoryColors = {
        "Programming": "#9e2f50",       // FT Red/Pink
        "AI & ML": "#0d7680",           // FT Dark Teal/Blue
        "Web Development": "#7ebfcc",   // FT Mid Blue
        "Startups": "#f2dfce",          // FT Beige/Cream
        "Security": "#b8b4b0",          // FT Grey
        "DevOps": "#69404b",            // Darker Red/Brown
        "Data": "#cceeee",              // FT Light Blue
        "Ask HN": "#ffb81c",            // FT Yellow/Gold accent
        "Show HN": "#59334c",           // Dark Purple/Pink
        "Science & Research": "#a6806a", // Brownish Tone
        "Crypto & Web3": "#777777",     // Neutral Mid-Grey
        "Mobile Dev": "#e9decf",        // Lighter Beige
        "Hardware": "#d4ac87",          // Brownish/Tan
        "Design & UX": "#8b9ba5",       // Blue-Grey
        "Jobs & Careers": "#f7a481",    // Lighter Salmon/Orange
        "Tech Companies": "#3d5a5f"     // Darker Teal shade
    };
    
    // Generate fallback colors (muted tones)
    const getColor = (str) => {
        if (categoryColors[str]) {
            return categoryColors[str];
        }
        
        // Hash function for other categories
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
        }
        
        // Convert to muted HSL color
        const h = hash % 360;
        const s = 30 + (hash % 20); // Saturation between 30-50%
        const l = 65 + (hash % 15); // Lightness between 65-80%
        return `hsl(${h}, ${s}%, ${l}%)`;
    };
    
    // Define the main categories to show individually
    const mainCategories = Object.keys(categoryColors);
    
    // Process and group categories
    let otherCount = 0;
    
    // Sort categories by count (descending)
    categories
        .sort((a, b) => b.count - a.count)
        .forEach(cat => {
            // Show main categories and those with at least 2% of total
            if (mainCategories.includes(cat.name) || (cat.count / totalCount >= 0.02)) {
                labels.push(cat.name);
                data.push(cat.count);
                backgroundColor.push(getColor(cat.name));
            } else {
                // Group small categories as "Other"
                otherCount += cat.count;
            }
        });
    
    // Add "Other" category if there are small categories
    if (otherCount > 0) {
        labels.push("Other");
        data.push(otherCount);
        backgroundColor.push("#b8b4b0"); // Use FT Grey for other
    }
    
    // Create the chart
    if (window.categoriesChart) {
        window.categoriesChart.destroy();
    }
    
    window.categoriesChart = new Chart(ctx, {
        type: 'doughnut', 
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColor,
                borderWidth: 1,
                borderColor: getComputedStyle(document.documentElement).getPropertyValue('--bg-color')
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%', 
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: getComputedStyle(document.documentElement).getPropertyValue('--text-color'),
                        font: {
                            size: 14 // Increased legend font size
                        },
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const percentage = ((value / totalCount) * 100).toFixed(1);
                            return `${label}: ${value} stories (${percentage}%)`;
                        }
                    },
                    padding: 12,
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13
                    }
                }
            },
            elements: {
                arc: {
                    borderWidth: 1,
                    hoverOffset: 15
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
}

// Load top stories (recent high scores or all-time high scores)
async function loadTopStories(type = 'recent') {
    const container = document.getElementById(`top-stories-${type}`);
    container.innerHTML = '<div class="loader"></div>';
    
    // Call API to get top stories (we will update server.py later)
    const endpoint = type === 'recent' ? '/stats/top-recent' : '/stats/top-alltime';
    const stories = await fetchData(endpoint);
    
    if (!stories || !stories.length) {
        container.innerHTML = '<p>No top stories found.</p>';
        return;
    }
    
    // Clear loader
    container.innerHTML = '';
    
    // Render top stories
    stories.forEach((story, index) => {
        const storyEl = document.createElement('div');
        storyEl.className = 'top-story-item';
        
        const domain = story.url ? new URL(story.url).hostname.replace('www.', '') : '';
        
        storyEl.innerHTML = `
            <div class="top-story-score">
                <div class="top-story-points">${story.score}</div>
                <div class="top-story-rank">#${index + 1}</div>
            </div>
            <div class="top-story-content">
                <div class="top-story-title">
                    <a href="${story.url || '#'}" target="_blank" rel="noopener noreferrer">
                        ${story.title}
                    </a>
                    ${domain ? `<small>(${domain})</small>` : ''}
                </div>
                <div class="top-story-meta">
                    <span class="news-category">${story.category || 'Uncategorized'}</span>
                    <span class="story-author">by ${story.by || 'Anonymous'}</span>
                    <span class="story-time">${formatTimestamp(story.time)}</span>
                </div>
            </div>
        `;
        
        container.appendChild(storyEl);
    });
}

// Toggle modal visibility
function toggleStatsModal(show = true) {
    if (show) {
        statsModal.classList.add('show');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
        
        // Load stats data if available
        if (window.statsData) {
            // Update total stories count
            modalTotalStories.textContent = window.statsData.total_stories;
            
            // Create category pie chart
            renderCategoriesChart(window.statsData.categories);
            
            // Load top stories
            loadTopStories('recent');
            loadTopStories('alltime');
        } else {
            // If stats are not loaded yet, fetch them
            loadDetailedStats();
        }
    } else {
        statsModal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

// Load all detailed stats for the modal
async function loadDetailedStats() {
    // Fetch basic stats if not already available
    if (!window.statsData) {
        await loadStats();
    }
    
    if (window.statsData) {
        // Update total stories count
        modalTotalStories.textContent = window.statsData.total_stories;
        
        // Get Ask HN and Show HN counts
        const askHN = window.statsData.categories.find(cat => cat.name === 'Ask HN');
        const showHN = window.statsData.categories.find(cat => cat.name === 'Show HN');
        
        modalAskHnCount.textContent = askHN ? askHN.count : 0;
        modalShowHnCount.textContent = showHN ? showHN.count : 0;
        
        // Create category pie chart
        renderCategoriesChart(window.statsData.categories);
    }
    
    // Load top stories
    loadTopStories('recent');
    loadTopStories('alltime');
}

// Search form event listener
searchForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const query = searchInput.value.trim();
    
    if (query) {
        searchNews(query, currentCategory);
    } else {
        // If search query is empty, show regular news
        loadNews(currentCategory);
    }
});

// Fetch autocomplete suggestions
async function fetchAutocompleteSuggestions(query) {
    if (!query || query.trim().length < 1) {
        hideAutocomplete();
        return;
    }
    
    try {
        const endpoint = `/autocomplete?q=${encodeURIComponent(query)}`;
        const suggestions = await fetchData(endpoint);
        
        if (suggestions && suggestions.length > 0) {
            displayAutocompleteSuggestions(suggestions, query);
        } else {
            hideAutocomplete();
        }
    } catch (error) {
        console.error('Error fetching autocomplete suggestions:', error);
        hideAutocomplete();
    }
}

// Display autocomplete suggestions
function displayAutocompleteSuggestions(suggestions, query) {
    // Clear previous suggestions
    autocompleteContainer.innerHTML = '';
    
    // Highlight the matching part in suggestions
    suggestions.forEach((suggestion, index) => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.setAttribute('data-index', index);
        
        // Highlight the matched part
        const value = suggestion.value;
        const lowerValue = value.toLowerCase();
        const lowerQuery = query.toLowerCase();
        const startIndex = lowerValue.indexOf(lowerQuery);
        
        if (startIndex >= 0) {
            const beforeMatch = value.substring(0, startIndex);
            const match = value.substring(startIndex, startIndex + query.length);
            const afterMatch = value.substring(startIndex + query.length);
            
            item.innerHTML = `${beforeMatch}<span class="highlight">${match}</span>${afterMatch}`;
        } else {
            item.textContent = value;
        }
        
        item.addEventListener('click', () => {
            selectAutocompleteSuggestion(suggestion.value);
        });
        
        autocompleteContainer.appendChild(item);
    });
    
    // Show the container
    autocompleteContainer.classList.add('active');
}

// Hide autocomplete container
function hideAutocomplete() {
    autocompleteContainer.classList.remove('active');
    autocompleteContainer.innerHTML = '';
    selectedAutocompleteIndex = -1;
}

// Select a suggestion
function selectAutocompleteSuggestion(value) {
    searchInput.value = value;
    hideAutocomplete();
}

// Navigate through suggestions with keyboard
function handleAutocompleteKeyNavigation(event) {
    const items = document.querySelectorAll('.autocomplete-item');
    if (!items.length) return;
    
    // Remove selected class from all items
    items.forEach(item => item.classList.remove('selected'));
    
    // Up arrow
    if (event.key === 'ArrowUp') {
        event.preventDefault();
        selectedAutocompleteIndex = selectedAutocompleteIndex <= 0 ? items.length - 1 : selectedAutocompleteIndex - 1;
        items[selectedAutocompleteIndex].classList.add('selected');
    }
    // Down arrow
    else if (event.key === 'ArrowDown') {
        event.preventDefault();
        selectedAutocompleteIndex = selectedAutocompleteIndex >= items.length - 1 ? 0 : selectedAutocompleteIndex + 1;
        items[selectedAutocompleteIndex].classList.add('selected');
    }
    // Enter key
    else if (event.key === 'Enter' && selectedAutocompleteIndex >= 0) {
        event.preventDefault();
        selectAutocompleteSuggestion(items[selectedAutocompleteIndex].textContent);
        searchForm.dispatchEvent(new Event('submit'));
    }
    // Escape key
    else if (event.key === 'Escape') {
        hideAutocomplete();
    }
}

// Event Listeners
function setupEventListeners() {
    refreshBtn.addEventListener('click', () => {
        loadNews(currentCategory);
        loadStats();
    });

    themeToggle.addEventListener('click', () => {
        darkMode = !darkMode;
        localStorage.setItem('darkMode', darkMode);
        
        if (darkMode) {
            document.body.setAttribute('data-theme', 'dark');
            themeToggle.innerHTML = '<i class="bi bi-sun"></i>';
        } else {
            document.body.removeAttribute('data-theme');
            themeToggle.innerHTML = '<i class="bi bi-moon"></i>';
        }
    });

    updateLink.addEventListener('click', event => {
        event.preventDefault();
        updateData();
    });

    // Home link listener
    const homeLink = document.getElementById('home-link');
    if (homeLink) {
        homeLink.addEventListener('click', (event) => {
            event.preventDefault(); // Prevent default anchor behavior
            
            // Reset category state
            currentCategory = 'all';
            isSearchMode = false;
            currentSearchQuery = '';
            searchInput.value = ''; // Clear search input
            autocompleteContainer.innerHTML = '';
            autocompleteContainer.classList.remove('active');

            // Update UI
            document.querySelectorAll('.category-pill').forEach(pill => {
                if (pill.getAttribute('data-category') === 'all') {
                    pill.classList.add('active');
                } else {
                    pill.classList.remove('active');
                }
            });
            selectedCategory.textContent = '(All)';
            
            // Load default news view
            loadNews('all');
        });
    }

    // Category pills listener
    categoriesList.addEventListener('click', (event) => {
        if (event.target.classList.contains('category-pill')) {
            const pill = event.target;
            // Update UI
            document.querySelector('.category-pill.active').classList.remove('active');
            pill.classList.add('active');
            
            // Update state
            currentCategory = pill.getAttribute('data-category');
            selectedCategory.textContent = currentCategory === 'all' ? '(All)' : `(${currentCategory})`;
            isSearchMode = false; // Exit search mode when category changes
            currentSearchQuery = '';
            searchInput.value = '';
            autocompleteContainer.innerHTML = '';
            autocompleteContainer.classList.remove('active');
            
            // Load news with selected category
            loadNews(currentCategory);
        }
    });

    // Stats modal events
    viewStatsBtn.addEventListener('click', () => {
        toggleStatsModal(true);
    });

    modalClose.addEventListener('click', () => {
        toggleStatsModal(false);
    });

    // Close modal when clicking outside the content
    statsModal.addEventListener('click', (event) => {
        if (event.target === statsModal) {
            toggleStatsModal(false);
        }
    });

    // Close modal on escape key
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && statsModal.classList.contains('show')) {
            toggleStatsModal(false);
        }
    });

    // Tab switching in the stats modal
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all tabs
            document.querySelectorAll('.tab-btn').forEach(tb => tb.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
            
            // Add active class to clicked tab
            btn.classList.add('active');
            const tabName = btn.getAttribute('data-tab');
            document.getElementById(`top-stories-${tabName}`).classList.add('active');
        });
    });

    // Autocomplete setup
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.trim();
        
        // Clear any existing timeout
        if (autocompleteTimeout) {
            clearTimeout(autocompleteTimeout);
        }
        
        // Set a small delay to avoid making too many requests while typing
        autocompleteTimeout = setTimeout(() => {
            fetchAutocompleteSuggestions(query);
        }, 300);
    });
    
    // Keyboard navigation for autocomplete
    searchInput.addEventListener('keydown', handleAutocompleteKeyNavigation);
    
    // Close autocomplete when clicking outside
    document.addEventListener('click', (event) => {
        if (!event.target.closest('.search-input-container')) {
            hideAutocomplete();
        }
    });
}

// Initial Load
async function init() {
    await loadCategories();
    loadNews(currentCategory);
    setupEventListeners(); // Call setupEventListeners after initial loads
}

init();