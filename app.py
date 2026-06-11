import os
import sys
import subprocess
import base64
from pathlib import Path

import streamlit as st

from analyzer import suggest_moments

# ==================== COOKIES HANDLER (FLEXIBLE & SAFE) ====================
def load_cookies():
    """Load cookies safely.
    - Local: use cookies.txt if exists (no error if missing)
    - Streamlit: decode from YOUTUBE_COOKIES_BASE64 secret
    """
    cookies_path = Path("cookies.txt")

    # 1. Local mode - use cookies.txt if available
    if cookies_path.exists():
        return str(cookies_path)

    # 2. Streamlit Secrets mode (safe check)
    try:
        if "YOUTUBE_COOKIES_BASE64" in st.secrets:
            b64_content = st.secrets["YOUTUBE_COOKIES_BASE64"]
            decoded = base64.b64decode(b64_content).decode("utf-8", errors="ignore")

            # Write to cookies.txt
            cookies_path.write_text(decoded, encoding="utf-8")
            st.success("✅ Cookies loaded from Streamlit Secrets")
            return str(cookies_path)
    except Exception:
        pass  # Ignore if secrets not available (local mode)

    return None

COOKIES_FILE = load_cookies()
# ==================== END COOKIES HANDLER ====================

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

        if st.button("➕ Add Clip"):
            start_sec = mmss_to_sec(start_time)
            end_sec = mmss_to_sec(end_time)
            duration = end_sec - start_sec
            if duration > 0:
                st.session_state.manual_clips.append({
                    "start": start_sec,
                    "duration": duration
                })
                st.success(f"Added clip {len(st.session_state.manual_clips)}")

        if st.session_state.manual_clips:
            st.write("**Clips added:**")
            for i, clip in enumerate(st.session_state.manual_clips):
                st.write(f"{i+1}. {clip['start']}s → {clip['start'] + clip['duration']}s")

# ==================== GENERATE BUTTON ====================
if st.button("🚀 Generate Clips", type="primary"):
    if not url:
        st.error("Please enter a YouTube URL")
        st.stop()

    # Download
    try:
        os.makedirs("downloads", exist_ok=True)
        downloaded = "downloads/original.mp4"

        format_map = {
            "360p": "best[height<=360]",
            "480p": "best[height<=480]",
            "720p": "best[height<=720]",
            "1080p": "best[height<=1080]"
        }
        format_selector = format_map.get(quality_choice, "best[height<=720]")

        cmd = [
            "yt-dlp",
            "-f", format_selector,
            "-o", downloaded,
            "--merge-output-format", "mp4",
            "--no-check-certificate",
            "--user-agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
            url
        ]

        # Add cookies if available
        if COOKIES_FILE:
            cmd.extend(["--cookies", COOKIES_FILE])

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

    # Save to session (using bytes)
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
            st.video(data["bytes"], format="video/mp4")
            st.download_button(
                f"⬇️ Download {i+1}",
                data=data["bytes"],
                file_name=data["name"],
                mime="video/mp4",
                key=f"dl_{i}"
            )