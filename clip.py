import os
import subprocess
import yt_dlp

def download_and_clip(url, output_name=None):
    os.makedirs("downloads", exist_ok=True)

    # 1. Download video dulu
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'merge_output_format': 'mp4',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        downloaded_file = ydl.prepare_filename(info)

    print(f"✅ Video downloaded: {downloaded_file}")

    # 2. Jalankan auto-editor ke file yang sudah di-download
    output_path = f"downloads/{output_name}.mp4" if output_name else downloaded_file.replace(".mp4", "_clipped.mp4")

    cmd = [
        "python3", "-m", "auto_editor",
        downloaded_file,
        "--output", output_path,
        "--no-open"
    ]

    print("🚀 Running auto-editor...")
    subprocess.run(cmd, check=True)

    print(f"✅ Done! File saved at: {output_path}")
    return output_path


if __name__ == "__main__":
    url = input("Paste YouTube URL: ").strip()
    name = input("Output filename (optional): ").strip() or None
    download_and_clip(url, name)
