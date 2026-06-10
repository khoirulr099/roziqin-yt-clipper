import sys
import os
import subprocess

def auto_clip_youtube(url):
    downloads_folder = "downloads"
    os.makedirs(downloads_folder, exist_ok=True)

    print(f"📥 Downloading: {url}")
    
    # Download video using yt-dlp
    download_cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
        "-o", f"{downloads_folder}/%(title)s.%(ext)s",
        url
    ]
    
    subprocess.run(download_cmd, check=True)
    
    # Find the downloaded file
    files = [f for f in os.listdir(downloads_folder) if f.endswith(".mp4")]
    if not files:
        print("❌ No video found after download!")
        return
    
    latest_file = max([os.path.join(downloads_folder, f) for f in files], key=os.path.getctime)
    output_file = latest_file.replace(".mp4", "_clipped.mp4")
    
    print(f"✂️ Auto clipping: {latest_file}")
    
    # Run auto-editor
    clip_cmd = [
        "auto-editor",
        latest_file,
        "--export", "mp4",
        "-o", output_file
    ]
    
    subprocess.run(clip_cmd, check=True)
    print(f"✅ Done! Saved as: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python auto_clip.py <youtube_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    auto_clip_youtube(url)
