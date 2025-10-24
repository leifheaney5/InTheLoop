
# InTheLoop

**Your daily personalized news digest with a modern web interface and smart filtering.**

<img width="2494" height="1290" alt="firefox_pWW9LI1QHY" src="https://github.com/user-attachments/assets/0816dbe9-4990-4b69-9da7-dfe627b936ac" />

---

## ✨ Features

### 📰 Expanded Content Coverage
- **8 News Categories**: Technology, Finance, General News, Sports, Science, Business, Entertainment, and Health
- **50+ Premium RSS Sources**: Curated feeds from top publications
- **Real-time Updates**: Articles cached for 30 minutes with manual refresh option

### 🎨 Modern Web Interface
- **Beautiful Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Dark/Light Theme**: Toggle between themes with persistent preference
- **Smooth Animations**: Professional transitions and micro-interactions
- **Gradient Badges**: Category-coded color schemes for easy scanning

### 🔍 Advanced Filtering
- **Category Filtering**: Click any category to focus on specific topics
- **Live Search**: Real-time search across titles and summaries
- **Smart Results**: Instant filtering without page reloads
- **Keyboard Shortcuts**: `Ctrl+K` to focus search, `Esc` to clear

### 📧 Email Integration
- **Daily Digest**: Automated email delivery at 9:00 AM
- **HTML Formatting**: Beautiful, responsive email templates
- **Customizable Schedule**: Easy to adjust timing in code

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.8+** installed
- **Git** (optional, for cloning)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/InTheLoop.git
cd InTheLoop

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the project root:

```env
SENDER_EMAIL=your_gmail_address@gmail.com
APP_PASSWORD=your_gmail_app_password
RECEIVER_EMAIL=recipient_email_address@gmail.com
```

> **📧 Gmail Users**: Use an [App Password](https://myaccount.google.com/apppasswords) if you have 2FA enabled (NOT your regular password).

### 4. Run the Application

```bash
python main.py
```

The web interface will be available at: **http://localhost:5000**

---

## 🎯 Usage

### Web Interface
1. Open your browser to `http://localhost:5000`
2. Browse articles from all categories or filter by specific topics
3. Use the search bar to find articles by keyword
4. Click category badges to filter content
5. Toggle between light/dark themes with the moon/sun icon
6. Click "Read More" on any article to view the full story

### Email Delivery
- Emails are automatically sent daily at 9:00 AM
- To test immediately, refresh the page or restart the server
- Email contains all articles formatted in a clean, readable layout

---

## 📱 Mobile Experience

InTheLoop is fully responsive and optimized for mobile devices:
- ✅ Touch-friendly interface
- ✅ Swipeable category filters
- ✅ Optimized card layouts
- ✅ Fast loading times
- ✅ Readable typography

---

## ⚙️ Customization

### Adding/Removing RSS Feeds

Edit the `rss_feeds` dictionary in `main.py`:

```python
rss_feeds = {
    "Your Category": [
        "https://example.com/feed.xml",
        "https://another-source.com/rss"
    ]
}
```

### Changing Email Schedule

Modify the schedule line in `main.py`:

```python
# Change from 9:00 AM to your preferred time
schedule.every().day.at("06:00").do(job)  # 6 AM
```

### Adjusting Cache Duration

Update the cache timeout in the `fetch_articles` function:

```python
if age < timedelta(minutes=60):  # Change from 30 to 60 minutes
```

---

## 🛠️ Technology Stack

- **Backend**: Python 3.8+, Flask
- **Frontend**: Vanilla JavaScript, CSS3, HTML5
- **RSS Parsing**: feedparser
- **Email**: smtplib with HTML templates
- **Scheduling**: schedule library
- **Icons**: Font Awesome 6
- **Fonts**: Inter (Google Fonts)

---

## 🔧 Automation

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create a new task to run `python main.py` at startup
3. Set it to run whether user is logged in or not

### Linux/Mac (cron)
```bash
# Add to crontab (crontab -e)
@reboot cd /path/to/InTheLoop && python3 main.py
```

### Docker (Coming Soon)
We're working on Docker support for even easier deployment!

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Change the port in main.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Email Not Sending
- Verify your `.env` file is in the correct location
- Confirm you're using an App Password (not your regular password)
- Check that your Gmail account has "Less secure app access" enabled if needed

### Articles Not Loading
- Check your internet connection
- Some RSS feeds may be temporarily unavailable
- Try the refresh button to force a new fetch

---

## 📝 License

This project is open source and available under the MIT License.

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Add new RSS feed sources

---

## 💡 Support
- Developer: Leif Heaney  
  Contact: leif@leifheaney.com
  Portfolio: [www.leifheaney.com](https://leifheaney.com/)
  GitHub: https://github.com/leifheaney5

---

**Stay up to date with your daily news using InTheLoop!**


