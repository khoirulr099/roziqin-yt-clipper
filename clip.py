import os
import yt_dlp

def get_strong_ydl_opts():
    """Strong yt-dlp options to avoid 429 and bot detection"""
    return {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'merge_output_format': 'mp4',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.youtube.com/',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android', 'web'],
                'player_skip': ['configs', 'webpage'],
            }
        },
        'sleep_requests': 1,
        'retries': 5,
        'fragment_retries': 5,
        'http_chunk_size': 10485760,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'no_warnings': False,
        'quiet': False,
    }

def download_and_clip(url, output_name=None):
    os.makedirs("downloads", exist_ok=True)

    ydl_opts = get_strong_ydl_opts()

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        downloaded_file = ydl.prepare_filename(info)

    print(f"✅ Video downloaded: {downloaded_file}")

    # 2. Jalankan auto-editor
    output_path = f"downloads/{output_name}.mp4" if output_name else downloaded_file.replace(".mp4", "_clipped.mp4")

    cmd = [
        "python3", "-m", "auto_editor",
        downloaded_file,
        "--output", output_path,
        "--no-open"
    ]

    print(f"🎬 Running auto-editor: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    print(f"✅ Clipped video saved: {output_path}")
    return output_path
