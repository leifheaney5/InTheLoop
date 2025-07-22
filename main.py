import os
import time
import logging
import feedparser
import schedule
import tkinter as tk
import webbrowser
try:
    from tkinterweb import HtmlFrame
    HAS_HTML = True
except ImportError:
    HAS_HTML = False

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import smtplib

load_dotenv()

logging.basicConfig(level=logging.INFO)

# add or drop RSS feeds as desired
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
        "https://feeds.marketwatch.com/marketwatch/topstories/",             # MarketWatch Top Stories
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
        "https://www.reuters.com/reuters/topNews",                            # Reuters Top News :contentReference[oaicite:3]{index=3}
        # U.S. & Regional
        "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
        "https://www.theguardian.com/us-news/rss",
        # Wire Services & Aggregators
        "https://news.google.com/rss",
        "https://apnews.com/apf-topnews",
        "https://www.npr.org/rss/rss.php?id=1001"
    ]
}

def fetch_articles():
    articles = []
    for category, urls in rss_feeds.items():
        for url in urls:
            logging.info(f"Fetching: {url}")
            feed = feedparser.parse(url)
            if feed.bozo:
                logging.warning(f"Bad feed, skipping: {url}")
                continue
            for entry in feed.entries[:5]:
                try:
                    articles.append({
                        'title': entry.title,
                        'author': getattr(entry, 'author', 'N/A'),
                        'link': entry.link,
                        'summary': entry.summary
                    })
                except AttributeError as e: #skip any articles that are missing attributes (ie. summary content)
                    logging.warning(f"Missing attribute in entry from {url} (title: {getattr(entry, 'title', 'N/A')}): {e}. Skipping entry.") 
    return articles

def create_email_content(articles):
    article_html = ""
    for art in articles:
        article_html += f"""
        <h3><a href="{art['link']}">{art['title']}</a></h3>
        <p>{art['summary']}</p>
        <hr>
        """
    return f"""
    <html>
      <body>
        <h2>InTheLoop - Your Daily News Briefing</h2>
        {article_html}
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

def job():
    arts = fetch_articles()
    if arts:
        html = create_email_content(arts)
        send_email(html) # Send email (SMTP) with the articles showing RSS headlines
        show_popup(arts)    
    else:
        logging.warning("No articles fetched.")

# Simple popup to show RSS headlines
def show_popup(articles):
    # Group articles by section and add site info
    from collections import defaultdict
    grouped = defaultdict(list)
    # Build a mapping from domain to section
    domain_to_section = {}
    for section, urls in rss_feeds.items():
        for url in urls:
            domain = url.split('/')[2]
            domain_to_section[domain] = section

    def get_domain(url):
        return url.split('/')[2]

    for art in articles:
        domain = get_domain(art['link'])
        section = domain_to_section.get(domain, 'Other')
        art['site'] = domain
        grouped[section].append(art)

    # Build HTML content
    html = """
    <html><head><style>
    body { font-family: Arial, sans-serif; }
    h2 { color: #2a5d9f; }
    h3 { margin-bottom: 0; }
    ul { margin-top: 0; }
    a { color: #1a0dab; text-decoration: underline; }
    .site { color: #555; font-size: 0.95em; }
    </style></head><body>
    <h2>InTheLoop - Daily News Briefing</h2>
    """
    for section in ['Technology', 'Finance', 'General News', 'Other']:
        if section in grouped:
            html += f'<h3>{section}</h3><ul>'
            for art in grouped[section]:
                html += f'<li><a href="{art["link"]}" target="_blank">{art["title"]}</a> <span class="site">({art["site"]})</span></li>'
            html += '</ul>'
    html += "</body></html>"

    if HAS_HTML:
        root = tk.Tk()
        root.title("InTheLoop - Daily News Briefing")
        root.geometry("700x500")
        frame = HtmlFrame(root, horizontal_scrollbar="auto")
        frame.set_content(html)
        frame.pack(fill="both", expand=True)
        root.mainloop()
    else:
        # Fallback: open in browser
        import tempfile
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html') as f:
            f.write(html)
            temp_path = f.name
        webbrowser.open(f'file://{temp_path}')


# Schedule popup and email for 9am daily
schedule.every().day.at("09:00").do(job)

if __name__ == "__main__":
    job()
