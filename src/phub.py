import yt_dlp
import os

def download_phub_video(url, output_path='downloads/%(title).80s.%(ext)s'):
    # Ensure output folder exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    ydl_opts = {
        'outtmpl': output_path,  # Save directly to SSD
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

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"Downloading: {url}")
        ydl.download([url])

if __name__ == "__main__":
    url = input("Enter Pornhub video URL: ").strip()
    download_phub_video(url)
