# Multi-Platform Video Downloader

Supports downloading videos from Pornhub, Facebook, Instagram, TikTok with cookie support for Pornhub.

## Features
- Low CPU usage with threading and asynchronous downloads
- Auto-delete downloaded files after user downloads or after 30 minutes
- Uses yt-dlp for video extraction
- Simple Flask web interface

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Add your Pornhub `.netscape` cookie file as `phub_cookies.netscape` in project root.

3. Run the Flask app:

```bash
python app.py
```

4. Visit `http://localhost:5000` in your browser.

## Notes

- The app cleans up downloads every 5 minutes.
- Downloads start async; the frontend polls status every 3 seconds.
- Download files are deleted 10 seconds after user downloads or after 30 mins if unused.