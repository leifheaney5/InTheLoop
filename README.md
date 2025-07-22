
# InTheLoop

**Your daily personalized news digest, delivered simple desktop popup and/or email.**

---

## Features
- Fetches top headlines from Technology, Finance, and General News RSS feeds.
- Pops up a modern, intuitive desktop window with clickable headlines.
- Sends a beautiful, regularly-scheduled email to your inbox every morning.
- Easy to configure and run on your own machine.
- Add or remove RSS feeds at will to tailor your inbox/ 

## Quick Start

1. **Clone this repository**
2. **Install Python 3.8+** (if not already installed)
3. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```
   (If you want the best popup experience, also run: `pip install tkinterweb`)

4. **Set up your environment variables:**
   - Create a file named `.env` in the project folder with:
     ```
     SENDER_EMAIL=your_gmail_address@gmail.com
     APP_PASSWORD=your_gmail_app_password
     RECEIVER_EMAIL=recipient_email_address@gmail.com
     ```
   - **Gmail users:** You must use an [App Password](https://myaccount.google.com/apppasswords) (NOT your regular gmail password) IF you have 2FA enabled.

5. **Run the app:**
   ```bash
   python main.py
   ```
   - By default, the news will be sent and shown at 9:00am ET every day.
   - To test instantly, change the schedule or call the `job()` function directly in `main.py`.

---

## Automation
- For daily automation, use Windows Task Scheduler or a cron job to run `main.py` at your preferred time.

---

## Support
- Developer: Leif Heaney  
  Contact: leif@leifheaney.com
  Portfolio: [www.leifheaney.com](https://leifheaney.com/)
  GitHub: https://github.com/leifheaney5

---

**Stay up to date with your daily news using InTheLoop!**


