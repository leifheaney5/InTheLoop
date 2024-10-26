import feedparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

# List of RSS feed URLs
rss_feeds = [
    'https://rss.cnn.com/rss/edition.rss',
    'https://feeds.bbci.co.uk/news/rss.xml',
    # Add more feeds here
]

def fetch_articles():
    articles = []
    for feed_url in rss_feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:  # Get top 5 articles from each feed
            articles.append({
                'title': entry.title,
                'link': entry.link,
                'summary': entry.summary
            })
    return articles

def create_email_content(articles):
    html_content = """
    <html>
        <head></head>
        <body>
            <h2>Today's News Briefing</h2>
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
    sender_email = 'leif@leifheaney.com'
    receiver_email = 'leif@leifheaney.com'
    password = os.environ.get('Easycheese123!$')

    message = MIMEMultipart('alternative')
    message['Subject'] = "In the Loop - Daily News Briefing"
    message['From'] = sender_email
    message['To'] = receiver_email

    part = MIMEText(html_content, 'html')
    message.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email,
            receiver_email,
            message.as_string()
        )

if __name__ == "__main__":
    articles = fetch_articles()
    email_content = create_email_content(articles)
    send_email(email_content)
