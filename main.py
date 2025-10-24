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
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Fetch initial articles
    logging.info("Fetching initial articles...")
    fetch_articles()
    
    # Start Flask web server
    logging.info("Starting web server at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
