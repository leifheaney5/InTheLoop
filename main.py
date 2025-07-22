import os
import time
import logging
import feedparser
import schedule

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import smtplib

load_dotenv()

logging.basicConfig(level=logging.INFO)

# add or drop RSS feeds as desired
rss_feeds = {
    "Tech": [
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

    "Stocks & Investors": [
        # Market News & Breaking Analysis
        "https://feeds.marketwatch.com/marketwatch/topstories/",                # MarketWatch Top Stories
        "https://www.reuters.com/markets/rss",                                # Reuters Markets :contentReference[oaicite:0]{index=0}
        "https://finance.yahoo.com/news/rssindex",                           # Yahoo Finance Market News
        "https://seekingalpha.com/feed.xml",                                 # Seeking Alpha Latest Ideas :contentReference[oaicite:1]{index=1}
        # TV & Web Financial Coverage
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",             # CNBC Top News & Analysis
        "https://news.alphastreet.com/feed",                                 # AlphaStreet Market Coverage :contentReference[oaicite:2]{index=2}
        "https://www.investors.com/feed/"                                    # Investor’s Business Daily
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
    for url in rss_feeds:
        logging.info(f"Fetching: {url}")
        feed = feedparser.parse(url)
        if feed.bozo:
            logging.warning(f"Bad feed, skipping: {url}")
            continue
        for entry in feed.entries[:5]:
            articles.append({
                'title': entry.title,
                'author': getattr(entry, 'author', 'N/A'),
                'link': entry.link,
                'summary': entry.summary
            })
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
    msg['Subject'] = "In the Loop – Daily Tech News Briefing"
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
        send_email(html)
    else:
        logging.warning("No articles fetched.")

# Schedule
schedule.every().day.at("08:00").do(job)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(60)
