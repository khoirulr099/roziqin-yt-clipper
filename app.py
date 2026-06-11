import os
import sys
import subprocess
import base64
from pathlib import Path
import tempfile

import streamlit as st
from analyzer import suggest_moments

# ==================== COOKIES HANDLER ====================
def load_cookies():
    """Load cookies from Streamlit Secrets (base64) if available"""
    cookies_path = Path("cookies.txt")
    
    if cookies_path.exists():
        return str(cookies_path)
    
    try:
        if "YOUTUBE_COOKIES_BASE64" in st.secrets:
            b64_data = st.secrets["YOUTUBE_COOKIES_BASE64"]
            decoded = base64.b64decode(b64_data)
            cookies_path.write_bytes(decoded)
            st.success("✅ Cookies loaded from Secrets")
            return str(cookies_path)
    except Exception as e:
        st.warning(f"⚠️ Failed to load cookies: {e}")
    
    return None

COOKIES_FILE = load_cookies()
# ========================================================

def get_yt_dlp_cmd(url, output_path):
    """Build yt-dlp command with strong options + cookies if available"""
    cmd = [
        sys.executable, "-m", "yt_dlp",
        url,
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "-o", output_path,
        "--merge-output-format", "mp4",
        "--user-agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "--referer", "https://www.youtube.com/",
        "--extractor-args", "youtube:player_client=ios,android,web",
        "--sleep-requests", "1",
        "--retries", "5",
        "--no-warnings",
    ]
    
    if COOKIES_FILE:
        cmd.extend(["--cookies", COOKIES_FILE])
    
    return cmd

st.set_page_config(page_title="Roziqin YouTube Clipper", layout="wide")
st.title("🎬 Roziqin YouTube Clipper")

url = st.text_input("YouTube URL")

if url and st.button("Download"):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "%(title)s.%(ext)s")
        cmd = get_yt_dlp_cmd(url, output_path)
        
        with st.spinner("Downloading..."):
            result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            st.success("Download berhasil!")
            # Lanjutkan proses clipping di sini
        else:
            st.error("Download gagal")
            st.code(result.stderr)