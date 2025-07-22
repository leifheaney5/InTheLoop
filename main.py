import os
import time
import logging
import feedparser
import schedule

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import smtplib

# Load environment variables
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)

# RSS feeds
rss_feeds = [
    'https://feeds.feedburner.com/TechCrunch/startups',
    'https://www.theverge.com/rss/index.xml',
    'https://rss.cnn.com/rss/cnn_tech.rss',
    'https://www.wired.com/feed/category/tech/latest/rss',
    'https://feeds.feedburner.com/ArsTechnica/Technology',
    'https://www.engadget.com/rss.xml',
    'https://www.bbc.co.uk/news/technology/rss.xml',
    'https://techcrunch.com/feed/',
    'https://www.cnet.com/rss/news/',
    'https://www.zdnet.com/feed/',
    'https://www.infoworld.com/index.rss',
    'https://www.thedrum.com/rss/technology',
    'https://www.fastcompany.com/rss',
    'https://www.siliconrepublic.com/feed',
    'https://www.ibm.com/blogs/9/rss/ai/',
]

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
        <h2>In The Loop – Daily Tech News Briefing</h2>
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
