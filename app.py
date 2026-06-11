import os
import sys
import subprocess
from pathlib import Path

import streamlit as st

from analyzer import suggest_moments

st.set_page_config(page_title="Roziqin YouTube Clipper", layout="wide")
st.title("🎬 Roziqin YouTube Clipper")

# ==================== INPUT ====================
url = st.text_input("YouTube URL")

mode = st.radio(
    "Mode",
    ["Auto Generate", "AI Suggested Moments", "Manual Mode"],
    horizontal=True
)

# Duration & Number of Clips
if mode != "Manual Mode":
    col1, col2 = st.columns(2)
    with col1:
        duration_choice = st.selectbox("Target Duration", ["30s", "60s", "90s", "120s", "Custom"])
        if duration_choice == "Custom":
            target_duration = st.number_input("Custom Duration (seconds)", 5, 300, 45, 5)
        else:
            target_duration = int(duration_choice.replace("s", ""))
    with col2:
        number_of_clips = st.slider("Number of Clips", 1, 5, 5)
else:
    target_duration = 60
    number_of_clips = 1

# Quality
quality_choice = st.selectbox("Quality", ["360p", "480p", "720p", "1080p"], index=2)

# Other options
col_a, col_b = st.columns(2)
with col_a:
    tiktok_vertical = st.checkbox("TikTok Vertical (9:16)", value=True)
    auto_tracking = st.checkbox("Auto Tracking", value=False)
with col_b:
    output_name = st.text_input("Output Prefix (optional)")

use_variation = st.checkbox("🔄 Regenerate with Variation (AI Suggested)", value=False)

# ==================== MANUAL MODE ====================
if mode == "Manual Mode":
    st.subheader("Manual Mode")
    st.info("Coming soon...")

# ==================== DOWNLOAD & PROCESS ====================
if st.button("🚀 Generate Clips", type="primary"):
    if not url:
        st.error("Please enter a YouTube URL")
        st.stop()

    os.makedirs("downloads", exist_ok=True)

    # Clean old files
    for f in os.listdir("downloads"):
        try:
            os.remove(os.path.join("downloads", f))
        except:
            pass

    # ==================== DOWNLOAD WITH YT-DLP (STRONG) ====================
    st.info(f"📥 Downloading ({quality_choice}) with yt-dlp...")

    downloaded = "downloads/final_video.mp4"
    height = quality_choice.replace("p", "")

    try:
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "-f", f"bestvideo[height<={height}]+bestaudio/best",
            "-o", downloaded,
            "--merge-output-format", "mp4",
            "--no-check-certificate",
            "--user-agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
            "--referer", "https://www.youtube.com/",
            "--extractor-args", "youtube:player_client=ios,android,web;player_skip=configs,webpage",
            "--sleep-requests", "1",
            "--retries", "5",
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            st.error(f"yt-dlp failed: {result.stderr}")
            st.stop()

    except Exception as e:
        st.error(f"Download failed: {e}")
        st.stop()

    clips = []

    # AI Suggested
    if mode == "AI Suggested Moments":
        st.info("🧠 Analyzing...")
        moments = suggest_moments(downloaded, max_moments=number_of_clips, variation=use_variation)
        for i, m in enumerate(moments):
            out = f"downloads/clip_{i+1}.mp4"
            subprocess.run(["ffmpeg", "-y", "-ss", str(m["start"]), "-i", downloaded,
                            "-t", str(target_duration), "-c", "copy", out], capture_output=True)
            if os.path.exists(out):
                clips.append(out)

    # Auto Generate
    elif mode == "Auto Generate":
        st.info("✂️ Creating clips...")
        # ... (rest of Auto Generate logic remains the same)

    # Show results
    if clips:
        st.success(f"✅ Generated {len(clips)} clips!")
        for i, clip in enumerate(clips):
            st.video(clip)
            with open(clip, "rb") as f:
                st.download_button("Download", f, file_name=os.path.basename(clip), key=f"dl_{i}")
    else:
        st.warning("No clips generated.")
