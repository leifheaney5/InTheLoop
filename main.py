import os
import time
import logging
import feedparser
import schedule
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import smtplib
import threading
from collections import defaultdict

load_dotenv()

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Expanded RSS feeds with more categories
rss_feeds = {
    "Technology": [
        # Startups & Analysis
        "https://techcrunch.com/feed/",
        # Product & Gadget Coverage
        "https://www.theverge.com/rss/index.xml",
        "https://www.engadget.com/rss.xml",
        # Deep‑dive & Labs
        "https://feeds.arstechnica.com/arstechnica/technology-lab",
        # Industry Trends & Reviews
        "https://www.wired.com/feed/category/tech/latest/rss",
        "https://www.technologyreview.com/feed/",
        # Community & Hacker Culture
        "https://news.ycombinator.com/rss"
    ],

    "Finance": [
        # Market News & Breaking Analysis
        "https://feeds.marketwatch.com/marketwatch/topstories/",
        "https://www.reuters.com/markets/rss",
        "https://finance.yahoo.com/news/rssindex",
        "https://seekingalpha.com/feed.xml",
        # TV & Web Financial Coverage
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://news.alphastreet.com/feed",
        "https://www.investors.com/feed/"
    ],

    "General News": [
        # Global & World
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.cnn.com/rss/cnn_topstories.rss",
        "https://www.reuters.com/reuters/topNews",
        # U.S. & Regional
        "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
        "https://www.theguardian.com/us-news/rss",
        # Wire Services & Aggregators
        "https://news.google.com/rss",
        "https://apnews.com/apf-topnews",
        "https://www.npr.org/rss/rss.php?id=1001"
    ],
    
    "Sports": [
        "https://www.espn.com/espn/rss/news",
        "https://www.cbssports.com/rss/headlines/",
        "https://www.si.com/rss/si_topstories.rss",
        "https://bleacherreport.com/articles/feed",
        "https://www.thescore.com/rss/news"
    ],
    
    "Science": [
        "https://www.sciencedaily.com/rss/all.xml",
        "https://www.sciencenews.org/feed",
        "https://www.nature.com/nature.rss",
        "https://feeds.feedburner.com/ScienceDaily",
        "https://www.popsci.com/feed",
        "https://www.space.com/feeds/all"
    ],
    
    "Business": [
        "https://www.forbes.com/business/feed/",
        "https://www.businessinsider.com/rss",
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://fortune.com/feed/",
        "https://www.entrepreneur.com/latest.rss"
    ],
    
    "Entertainment": [
        "https://variety.com/feed/",
        "https://deadline.com/feed/",
        "https://www.hollywoodreporter.com/feed/",
        "https://ew.com/feed/",
        "https://www.rollingstone.com/feed/"
    ],
    
    "Health": [
        "https://www.health.com/rss",
        "https://feeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC",
        "https://www.medicalnewstoday.com/rss/news.xml",
        "https://www.healthline.com/rss",
        "https://www.prevention.com/rss.xml"
    ]
}

# Global cache for articles
articles_cache = []
cache_timestamp = None

# User's hidden feeds (persisted)
hidden_feeds = set()

# Available feeds that users can add
available_feeds = {
    "Technology": [
        {"url": "https://www.cnet.com/rss/news/", "name": "CNET"},
        {"url": "https://www.zdnet.com/news/rss.xml", "name": "ZDNet"},
        {"url": "https://www.techmeme.com/feed.xml", "name": "Techmeme"},
        {"url": "https://arstechnica.com/feed/", "name": "Ars Technica"},
    ],
    "Finance": [
        {"url": "https://www.fool.com/feeds/index.aspx", "name": "Motley Fool"},
        {"url": "https://www.wsj.com/xml/rss/3_7085.xml", "name": "Wall Street Journal"},
        {"url": "https://www.ft.com/?format=rss", "name": "Financial Times"},
    ],
    "General News": [
        {"url": "https://www.aljazeera.com/xml/rss/all.xml", "name": "Al Jazeera"},
        {"url": "https://www.independent.co.uk/rss", "name": "The Independent"},
        {"url": "https://www.usatoday.com/rss/", "name": "USA Today"},
    ],
    "Sports": [
        {"url": "https://www.skysports.com/rss/12040", "name": "Sky Sports"},
        {"url": "https://www.foxsports.com/rss", "name": "Fox Sports"},
        {"url": "https://www.goal.com/feeds/en/news", "name": "Goal.com"},
    ],
    "Science": [
        {"url": "https://phys.org/rss-feed/", "name": "Phys.org"},
        {"url": "https://www.scientificamerican.com/feed/", "name": "Scientific American"},
        {"url": "https://www.livescience.com/feeds/all", "name": "Live Science"},
    ],
    "Business": [
        {"url": "https://www.inc.com/rss/", "name": "Inc.com"},
        {"url": "https://hbr.org/feed", "name": "Harvard Business Review"},
        {"url": "https://www.fastcompany.com/rss", "name": "Fast Company"},
    ],
    "Entertainment": [
        {"url": "https://www.billboard.com/feed/", "name": "Billboard"},
        {"url": "https://www.vulture.com/feed/", "name": "Vulture"},
        {"url": "https://www.imdb.com/news/rss/", "name": "IMDb News"},
    ],
    "Health": [
        {"url": "https://www.mayoclinic.org/rss", "name": "Mayo Clinic"},
        {"url": "https://www.everydayhealth.com/rss/", "name": "Everyday Health"},
        {"url": "https://www.menshealth.com/rss/all.xml/", "name": "Men's Health"},
    ]
}

def load_hidden_feeds():
    """Load hidden feeds from file"""
    global hidden_feeds
    try:
        if os.path.exists('hidden_feeds.txt'):
            with open('hidden_feeds.txt', 'r') as f:
                hidden_feeds = set(line.strip() for line in f if line.strip())
    except Exception as e:
        logging.error(f"Error loading hidden feeds: {e}")

def save_hidden_feeds():
    """Save hidden feeds to file"""
    try:
        with open('hidden_feeds.txt', 'w') as f:
            for feed in hidden_feeds:
                f.write(f"{feed}\n")
    except Exception as e:
        logging.error(f"Error saving hidden feeds: {e}")

def fetch_articles(force_refresh=False):
    """Fetch articles from RSS feeds with caching"""
    global articles_cache, cache_timestamp
    
    # Return cached articles if less than 30 minutes old
    if not force_refresh and cache_timestamp and articles_cache:
        age = datetime.now() - cache_timestamp
        if age < timedelta(minutes=30):
            logging.info("Returning cached articles")
            return articles_cache
    
    articles = []
    domain_to_category = {}
    
    # Build domain to category mapping
    for category, urls in rss_feeds.items():
        for url in urls:
            domain = url.split('/')[2] if len(url.split('/')) > 2 else url
            domain_to_category[domain] = category
    
    for category, urls in rss_feeds.items():
        for url in urls:
            # Skip hidden feeds
            if url in hidden_feeds:
                logging.info(f"Skipping hidden feed: {url}")
                continue
                
            logging.info(f"Fetching: {url}")
            feed = feedparser.parse(url)
            if feed.bozo:
                logging.warning(f"Bad feed, skipping: {url}")
                continue
            
            for entry in feed.entries[:8]:  # Increased from 5 to 8 per feed
                try:
                    # Get publication date
                    pub_date = datetime.now()
                    try:
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            time_tuple = entry.published_parsed
                            pub_date = datetime(int(time_tuple[0]), int(time_tuple[1]), int(time_tuple[2]), 
                                              int(time_tuple[3]), int(time_tuple[4]), int(time_tuple[5]))
                        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                            time_tuple = entry.updated_parsed
                            pub_date = datetime(int(time_tuple[0]), int(time_tuple[1]), int(time_tuple[2]),
                                              int(time_tuple[3]), int(time_tuple[4]), int(time_tuple[5]))
                    except (ValueError, TypeError, IndexError):
                        # If date parsing fails, use current time
                        pass
                    
                    domain = url.split('/')[2] if len(url.split('/')) > 2 else url
                    
                    articles.append({
                        'title': entry.title,
                        'author': getattr(entry, 'author', 'N/A'),
                        'link': entry.link,
                        'summary': getattr(entry, 'summary', 'No summary available'),
                        'category': category,
                        'site': domain,
                        'published': pub_date.isoformat(),
                        'published_display': pub_date.strftime('%b %d, %Y %I:%M %p')
                    })
                except AttributeError as e:
                    logging.warning(f"Missing attribute in entry from {url}: {e}. Skipping entry.")
                except Exception as e:
                    logging.error(f"Error processing entry from {url}: {e}")
    
    # Update cache
    articles_cache = articles
    cache_timestamp = datetime.now()
    
    return articles

def create_email_content(articles):
    """Create HTML email content from articles"""
    import html
    from collections import defaultdict
    
    # Group articles by category
    grouped = defaultdict(list)
    for art in articles:
        grouped[art['category']].append(art)
    
    article_html = ""
    for category in sorted(grouped.keys()):
        article_html += f'<h2 style="color: #2563eb; margin-top: 30px;">{category}</h2>'
        for art in grouped[category]:
            # Escape HTML entities in title
            title = html.escape(art['title'])
            # Strip HTML tags from summary but keep the text
            import re
            summary = re.sub('<[^<]+?>', '', art['summary'])
            summary = html.unescape(summary)[:200] + '...' if len(summary) > 200 else html.unescape(summary)
            
            article_html += f"""
            <div style="margin-bottom: 20px; padding: 15px; background: #f5f7fa; border-left: 3px solid #2563eb;">
                <h3 style="margin-top: 0;">
                    <a href="{art['link']}" style="color: #1a1a1a; text-decoration: none;">{title}</a>
                </h3>
                <p style="color: #4a5568; margin: 10px 0;">{summary}</p>
                <p style="font-size: 12px; color: #a0aec0;">
                    <strong>{art['site']}</strong> • {art['published_display']}
                </p>
            </div>
            """
    
    return f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #ffffff; }}
          h1 {{ color: #2563eb; }}
          a {{ color: #2563eb; }}
        </style>
      </head>
      <body>
        <h1>InTheLoop - Your Daily News Briefing</h1>
        <p style="color: #4a5568;">Here are today's top stories from across {len(grouped)} categories:</p>
        {article_html}
        <hr style="margin-top: 40px; border: none; border-top: 1px solid #d1d5db;">
        <p style="text-align: center; color: #a0aec0; font-size: 12px;">
          You're receiving this because you subscribed to InTheLoop daily digest.
        </p>
      </body>
    </html>
    """

def send_email(html_content):
    sender = os.getenv('SENDER_EMAIL')
    receiver = os.getenv('RECEIVER_EMAIL')
    pwd = os.getenv('APP_PASSWORD')
    if not (sender and receiver and pwd):
        logging.error("Missing one of SENDER_EMAIL, RECEIVER_EMAIL, APP_PASSWORD")
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "InTheLoop - Your Daily News Briefing"
    msg['From'] = sender
    msg['To'] = receiver
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, pwd)
            server.sendmail(sender, receiver, msg.as_string())
        logging.info("Email sent!")
    except Exception as e:
        logging.error(f"Email error: {e}")

# Flask Routes
@app.route('/')
def index():
    """Main page route"""
    return render_template('index.html', categories=list(rss_feeds.keys()))

@app.route('/feeds')
def feeds_page():
    """Feed management page"""
    return render_template('feeds.html')

@app.route('/api/articles')
def get_articles_api():
    """API endpoint to fetch articles with filtering"""
    category = request.args.get('category', 'all')
    search = request.args.get('search', '').lower()
    
    articles = fetch_articles()
    
    # Filter by category
    if category != 'all':
        articles = [a for a in articles if a['category'] == category]
    
    # Filter by search term
    if search:
        articles = [a for a in articles if 
                   search in a['title'].lower() or 
                   search in a['summary'].lower()]
    
    return jsonify({
        'articles': articles,
        'count': len(articles),
        'cached': cache_timestamp.isoformat() if cache_timestamp else None
    })

@app.route('/api/refresh')
def refresh_articles():
    """Force refresh articles"""
    articles = fetch_articles(force_refresh=True)
    return jsonify({
        'success': True,
        'count': len(articles),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/feeds')
def get_feeds():
    """Get all RSS feeds with their status"""
    feeds_list = []
    for category, urls in rss_feeds.items():
        for url in urls:
            # Extract feed name from URL
            domain = url.split('/')[2] if len(url.split('/')) > 2 else url
            feeds_list.append({
                'url': url,
                'category': category,
                'name': domain,
                'hidden': url in hidden_feeds
            })
    return jsonify({
        'feeds': feeds_list,
        'total': len(feeds_list),
        'hidden_count': len(hidden_feeds)
    })

@app.route('/api/feeds/hide', methods=['POST'])
def hide_feed():
    """Hide a specific feed"""
    data = request.json
    feed_url = data.get('url')
    
    if not feed_url:
        return jsonify({'error': 'URL required'}), 400
    
    hidden_feeds.add(feed_url)
    save_hidden_feeds()
    
    # Force refresh articles
    fetch_articles(force_refresh=True)
    
    return jsonify({
        'success': True,
        'message': f'Feed hidden: {feed_url}',
        'hidden_count': len(hidden_feeds)
    })

@app.route('/api/feeds/unhide', methods=['POST'])
def unhide_feed():
    """Unhide a specific feed"""
    data = request.json
    feed_url = data.get('url')
    
    if not feed_url:
        return jsonify({'error': 'URL required'}), 400
    
    if feed_url in hidden_feeds:
        hidden_feeds.remove(feed_url)
        save_hidden_feeds()
        
        # Force refresh articles
        fetch_articles(force_refresh=True)
    
    return jsonify({
        'success': True,
        'message': f'Feed unhidden: {feed_url}',
        'hidden_count': len(hidden_feeds)
    })

@app.route('/api/feeds/available')
def get_available_feeds():
    """Get list of available feeds that can be added"""
    return jsonify({
        'feeds': available_feeds,
        'total': sum(len(feeds) for feeds in available_feeds.values())
    })

@app.route('/api/feeds/add', methods=['POST'])
def add_feed():
    """Add a new feed to the active feeds"""
    data = request.json
    feed_url = data.get('url')
    category = data.get('category')
    
    if not feed_url or not category:
        return jsonify({'error': 'URL and category required'}), 400
    
    if category not in rss_feeds:
        return jsonify({'error': 'Invalid category'}), 400
    
    # Add feed to the category if not already present
    if feed_url not in rss_feeds[category]:
        rss_feeds[category].append(feed_url)
        
        # Remove from hidden feeds if it was hidden
        if feed_url in hidden_feeds:
            hidden_feeds.remove(feed_url)
            save_hidden_feeds()
        
        # Force refresh articles
        fetch_articles(force_refresh=True)
        
        return jsonify({
            'success': True,
            'message': f'Feed added to {category}',
            'url': feed_url
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Feed already exists'
        }), 400

def job():
    """Scheduled job to send email"""
    arts = fetch_articles(force_refresh=True)
    if arts:
        html = create_email_content(arts)
        send_email(html)
        logging.info("Daily email sent successfully")
    else:
        logging.warning("No articles fetched for scheduled job.")

def run_scheduler():
    """Run the scheduler in a background thread"""
    while True:
        schedule.run_pending()
        time.sleep(60)

# Schedule email for 9am daily
schedule.every().day.at("09:00").do(job)

if __name__ == "__main__":
    # Load hidden feeds
    load_hidden_feeds()
    logging.info(f"Loaded {len(hidden_feeds)} hidden feeds")
    
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Fetch initial articles
    logging.info("Fetching initial articles...")
    fetch_articles()
    
    # Start Flask web server
    logging.info("Starting web server at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
