import os
import sys
import subprocess
import json
from pathlib import Path

# Force upgrade yt-dlp BEFORE importing (penting untuk Streamlit Cloud)
subprocess.run([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"], 
               capture_output=True)

import streamlit as st
import yt_dlp

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
QUALITY_MAP = {
    "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
}
format_selector = QUALITY_MAP[quality_choice]

# Other options
col_a, col_b = st.columns(2)
with col_a:
    tiktok_vertical = st.checkbox("TikTok Vertical (9:16)", value=True)
    auto_tracking = st.checkbox("Auto Tracking", value=False)
with col_b:
    output_name = st.text_input("Output Prefix (optional)")

use_variation = st.checkbox("🔄 Regenerate with Variation (AI Suggested)", value=False)

# ==================== MANUAL MODE ====================
if mode == "Manual Mode" and url:
    st.markdown("---")
    st.subheader("✂️ Manual Mode")

    col_video, col_control = st.columns([2, 1])

    with col_video:
        st.video(url)

    with col_control:
        if "manual_clips" not in st.session_state:
            st.session_state.manual_clips = []

        start_time = st.text_input("Start (MM:SS)", value="00:00")
        end_time = st.text_input("End (MM:SS)", value="01:00")

        def mmss_to_sec(mmss):
            try:
                m, s = map(int, mmss.split(":"))
                return m * 60 + s
            except:
                return 0

        if st.button("➕ Add Clip", key="add_manual"):
            start = mmss_to_sec(start_time)
            end = mmss_to_sec(end_time)
            if end > start:
                st.session_state.manual_clips.append({
                    "start": start,
                    "end": end,
                    "duration": end - start
                })
                st.success(f"Added: {start}s - {end}s")
            else:
                st.error("End must be greater than Start")

        if st.session_state.manual_clips:
            st.write(f"**{len(st.session_state.manual_clips)} clips** added")
            if st.button("🗑️ Reset All"):
                st.session_state.manual_clips = []
                st.rerun()

# ==================== PROCESS ====================
if st.button("🚀 Start Processing", type="primary"):
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

    # Download
    st.info(f"📥 Downloading ({quality_choice})...")

    ydl_opts = {
        "format": format_selector,
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "merge_output_format": "mp4",
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.youtube.com/",
            "Origin": "https://www.youtube.com",
            "Accept-Encoding": "gzip, deflate, br",
        },
        "nocheckcertificate": True,
        "quiet": False,
        "no_warnings": True,
        "sleep_interval_requests": 1,
        "extractor_args": {
            "youtube": {
                "player_client": ["ios", "mweb", "tv_embedded", "web"],
            }
        },
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded = ydl.prepare_filename(info)
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
        for i in range(number_of_clips):
            start = i * (target_duration + 10)
            out = f"downloads/clip_{i+1}.mp4"
            subprocess.run(["ffmpeg", "-y", "-ss", str(start), "-i", downloaded,
                            "-t", str(target_duration), "-c", "copy", out], capture_output=True)
            if os.path.exists(out):
                clips.append(out)

    # Manual Mode
    elif mode == "Manual Mode":
        if not st.session_state.get("manual_clips"):
            st.error("No manual clips added!")
            st.stop()
        st.info("✂️ Creating manual clips...")
        for i, clip in enumerate(st.session_state.manual_clips):
            out = f"downloads/manual_clip_{i+1}.mp4"
            subprocess.run(["ffmpeg", "-y", "-ss", str(clip["start"]), "-i", downloaded,
                            "-t", str(clip["duration"]), "-c", "copy", out], capture_output=True)
            if os.path.exists(out):
                clips.append(out)

    # TikTok Vertical
    if tiktok_vertical and clips:
        st.info("📱 Converting to Vertical...")
        final = []
        for c in clips:
            out = c.replace(".mp4", "_tiktok.mp4")
            subprocess.run(["ffmpeg", "-y", "-i", c,
                            "-vf", "scale=-1:1920,crop=1080:1920",
                            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                            "-c:a", "aac", "-b:a", "128k", out], capture_output=True)
            if os.path.exists(out):
                final.append(out)
        clips = final

    # Save to session
    if clips:
        st.session_state.clips_data = []
        for clip in clips:
            with open(clip, "rb") as f:
                st.session_state.clips_data.append({
                    "name": Path(clip).name,
                    "bytes": f.read()
                })
        # Clean downloads
        for f in os.listdir("downloads"):
            try:
                os.remove(os.path.join("downloads", f))
            except:
                pass
        st.success(f"✅ Created {len(clips)} clips")
    else:
        st.error("No clips were created")

# ==================== DISPLAY ====================
if "clips_data" in st.session_state and st.session_state.clips_data:
    st.subheader("🎥 Preview & Download")
    cols = st.columns(5)
    for i, data in enumerate(st.session_state.clips_data):
        with cols[i % 5]:
            st.write(f"**{data['name']}**")
            st.video(data["bytes"])
            st.download_button(
                f"⬇️ Download {i+1}",
                data=data["bytes"],
                file_name=data["name"],
                mime="video/mp4",
                key=f"dl_{i}"
            )