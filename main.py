import feedparser
import smtplib
import os
import logging

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables from .env file (optional)
load_dotenv()

# logging config 
logging.basicConfig(level=logging.INFO)

# add desired RSS feeds to list below in https web format 
rss_feeds = [

    # default RSS feeds
    'https://feeds.feedburner.com/TechCrunch/startups',  # TechCrunch Startups
    'https://www.theverge.com/rss/index.xml',  # The Verge
    'https://rss.cnn.com/rss/cnn_tech.rss',  # CNN Tech
    'https://www.wired.com/feed/category/tech/latest/rss',  # Wired Tech
    'https://feeds.feedburner.com/ArsTechnica/Technology',  # Ars Technica Technology
    'https://www.engadget.com/rss.xml',  # Engadget
    'https://www.bbc.co.uk/news/technology/rss.xml',  # BBC Technology News
    'https://techcrunch.com/feed/',  # TechCrunch
    'https://www.cnet.com/rss/news/',  # CNET News
    'https://www.zdnet.com/feed/',  # ZDNet
    'https://www.infoworld.com/index.rss',  # InfoWorld
    'https://www.thedrum.com/rss/technology',  # The Drum - Technology
    'https://www.fastcompany.com/rss',  # Fast Company Technology
    'https://www.siliconrepublic.com/feed',  # Silicon Republic
    'https://www.ibm.com/blogs/9/rss/ai/',  # IBM Blog - AI
]

def fetch_articles():
    """Fetch articles from RSS feeds."""
    articles = []
    try:
        for feed_url in rss_feeds:
            logging.info(f"Fetching feed: {feed_url}")
            feed = feedparser.parse(feed_url)
            if feed.bozo:
                logging.warning(f"Skipping over malfunctioning feed: {feed_url}")
                continue
            for entry in feed.entries[:5]:  # Get top 5 articles from each feed
                articles.append({
                    'title': entry.title,
                    'author': getattr(entry, 'author', 'N/A'),
                    'link': entry.link,
                    'summary': entry.summary,
                })
    except Exception as e:
        logging.error(f"Error fetching articles: {e}")
    return articles

def create_email_content(articles):
    html_content = """
    <html>
        <head></head>
        <body>
            <h2>In The Loop - Daily Tech News Briefing</h2>
            {}
        </body>
    </html>
    """
    article_entries = ""
    for article in articles:
        entry = f"""
        <h3><a href="{article['link']}">{article['title']}</a></h3>
        <p>{article['summary']}</p>
        <hr>
        """
        article_entries += entry
    return html_content.format(article_entries)

def send_email(html_content):
    """Send the email using SMTP."""
    sender_email = os.getenv('SENDER_EMAIL')  # replace with your gmail sender address
    receiver_email = os.getenv('RECEIVER_EMAIL')  # replace with any receiver email address
    password = os.getenv('APP_PASSWORD')  # use env var password via BASH

    if not all([sender_email, receiver_email, password]):
        logging.error("Email credentials are missing in environment variables.")
        return

    try:
        message = MIMEMultipart('alternative')
        message['Subject'] = "In the Loop - Daily Tech News Briefing"
        message['From'] = sender_email
        message['To'] = receiver_email

        part = MIMEText(html_content, 'html')
        message.attach(part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server: # gmail only
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Error sending email: {e}")

def job():
    """Job to fetch articles, create email content, and send the email."""
    articles = fetch_articles()
    if articles:
        email_content = create_email_content(articles)
        send_email(email_content)
    else:
        logging.warning("No articles to send.")

schedule.every().day.at("08:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)  # Wait for 1 minute before checking again


