import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_file, render_template, abort
import yt_dlp
import hashlib

app = Flask(__name__)

DOWNLOAD_FOLDER = "tmp/downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

cleanup_interval = 300  # 5 minutes
file_expiry = 1800      # 30 minutes

executor = ThreadPoolExecutor(max_workers=4)

download_locks = {}
download_status = {}

def cleanup_files():
    while True:
        now = time.time()
        for f in os.listdir(DOWNLOAD_FOLDER):
            fpath = os.path.join(DOWNLOAD_FOLDER, f)
            try:
                stat = os.stat(fpath)
                if now - stat.st_mtime > file_expiry:
                    os.remove(fpath)
            except Exception:
                pass
        time.sleep(cleanup_interval)

def hash_url(url):
    return hashlib.sha256(url.encode()).hexdigest()

def download_video(url, cookiefile=None):
    filename = hash_url(url) + ".mp4"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    if os.path.exists(filepath):
        # Update modification time for expiry reset
        os.utime(filepath, None)
        return filepath

    # Custom options for Pornhub (low CPU, chunked download, limited concurrency)
    if cookiefile and "phub_cookies.netscape" in cookiefile.lower():
        ydl_opts = {
            'outtmpl': output_path,  # Save directly to SSD
            'cookiefile': cookiefile,
            'format': 'best[ext=mp4]/best',  # Hardware-friendly codec
            'noplaylist': True,
            'quiet': False,
            'no_warnings': True,
            'restrictfilenames': True,
            'concurrent_fragment_downloads': 3,  # Limited threads = lower CPU
            'retries': 3,
            'http_chunk_size': 5 * 1024 * 1024,  # Chunked download (less memory overhead)
            'noprogress': True,  # Skip fancy progress = less CPU
            'nopart': True,  # No .part file (less disk I/O)  
        }
    else:
        # Default options for other sites
        ydl_opts = {
            'outtmpl': filepath,
            'format': 'best[ext=mp4]/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'cookiefile': cookiefile,
            'nocheckcertificate': True,
            'prefer_insecure': True,
            'retries': 2,
            'fixup': 'detect_or_warn',
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if os.path.exists(filepath):
            return filepath
    except Exception as e:
        print("Download error:", e)
        if os.path.exists(filepath):
            os.remove(filepath)
        return None

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download_route():
    data = request.json
    if not data or "url" not in data:
        return jsonify({"error": "Missing URL"}), 400

    url = data["url"].strip()
    cookiefile = None

    # For Pornhub use .netscape cookie file path
    if "pornhub.com" in url.lower():
        cookiefile = "phub_cookies.netscape"
        if not os.path.exists(cookiefile):
            return jsonify({"error": "Phub cookie file missing on server"}), 500

    hash_key = hash_url(url)

    # Prevent concurrent downloads of the same file
    if hash_key in download_locks:
        return jsonify({"status": "Downloading in progress, please wait"}), 202

    # Submit download task
    download_locks[hash_key] = True

    def task():
        path = download_video(url, cookiefile)
        if path:
            download_status[hash_key] = path
        else:
            download_status[hash_key] = None
        del download_locks[hash_key]

    executor.submit(task)
    return jsonify({"status": "Download started, check /status endpoint", "id": hash_key})

@app.route("/status/<file_id>", methods=["GET"])
def status(file_id):
    if file_id in download_status:
        if download_status[file_id]:
            return jsonify({"status": "ready", "download_url": f"/file/{file_id}"})
        else:
            return jsonify({"status": "error", "message": "Failed to download"})
    else:
        return jsonify({"status": "pending"})

@app.route("/file/<file_id>", methods=["GET"])
def serve_file(file_id):
    if file_id not in download_status or not download_status[file_id]:
        abort(404)
    filepath = download_status[file_id]

    if not os.path.exists(filepath):
        abort(404)

    def remove_file_after_send():
        try:
            time.sleep(10)
            if os.path.exists(filepath):
                os.remove(filepath)
            if file_id in download_status:
                del download_status[file_id]
        except Exception:
            pass

    threading.Thread(target=remove_file_after_send).start()
    return send_file(filepath, as_attachment=True)

if __name__ == "__main__":
    threading.Thread(target=cleanup_files, daemon=True).start()
    app.run(debug=True, host="0.0.0.0", port=5000)
