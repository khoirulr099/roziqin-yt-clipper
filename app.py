import os
import sys
import subprocess
import base64
import tempfile
from pathlib import Path

import streamlit as st

# ==================== COOKIES HANDLER ====================
def load_cookies():
    cookies_path = Path("cookies.txt")
    if cookies_path.exists():
        return str(cookies_path)
    try:
        if "YOUTUBE_COOKIES_BASE64" in st.secrets:
            b64_content = st.secrets["YOUTUBE_COOKIES_BASE64"]
            decoded = base64.b64decode(b64_content).decode("utf-8", errors="ignore")
            cookies_path.write_text(decoded, encoding="utf-8")
            return str(cookies_path)
    except Exception:
        pass
    return None

COOKIES_FILE = load_cookies()

# ==================== HELPERS ====================
def run_ffmpeg(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stderr

def is_valid_video(path):
    if not os.path.exists(path) or os.path.getsize(path) < 1024:
        return False
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1", path],
        capture_output=True, text=True
    )
    return result.returncode == 0 and "duration" in result.stdout

def get_video_resolution(path):
    """Return (width, height) of video"""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "csv=p=0", path],
        capture_output=True, text=True
    )
    try:
        w, h = result.stdout.strip().split(",")
        return int(w), int(h)
    except:
        return 0, 0

def clip_video(src, out, start, duration):
    ok, err = run_ffmpeg([
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", src,
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        out
    ])
    return ok, err

def convert_vertical(src, out):
    ok, err = run_ffmpeg([
        "ffmpeg", "-y", "-i", src,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        out
    ])
    return ok, err

def convert_tracking(src, out):
    # Crop 10% tepi sebagai buffer stabilisasi — no external library needed
    ok, err = run_ffmpeg([
        "ffmpeg", "-y", "-i", src,
        "-vf", (
            "crop=iw*0.9:ih*0.9,"
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920"
        ),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        out
    ])
    return ok, err

# ==================== FORMAT SELECTOR ====================
def build_format_selector(quality):
    """
    Build yt-dlp format string yang bener-bener sesuai kualitas pilihan.
    Priority: exact height mp4 → max height mp4 → fallback best
    """
    h = quality.replace("p", "")
    return (
        # Priority 1: exact height, mp4 video + m4a audio
        f"bestvideo[height={h}][ext=mp4]+bestaudio[ext=m4a]"
        # Priority 2: max height <= pilihan, mp4 + m4a
        f"/bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]"
        # Priority 3: exact height, any format → merge to mp4
        f"/bestvideo[height={h}]+bestaudio"
        # Priority 4: max height <= pilihan, any format
        f"/bestvideo[height<={h}]+bestaudio"
        # Fallback: single file best quality <= height
        f"/best[height<={h}]"
        # Last resort
        f"/best"
    )

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="Roziqin YT Clipper", layout="wide", page_icon="✂️")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
.stButton > button { border-radius: 8px; font-weight: 600; transition: transform 0.15s; }
.stButton > button:hover { transform: translateY(-1px); }
</style>
""", unsafe_allow_html=True)

st.title("🎬 Roziqin YouTube Clipper")

# ==================== INPUT ====================
url = st.text_input("🔗 YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

mode = st.radio(
    "Mode",
    ["Auto Generate", "AI Suggested Moments", "Manual Mode"],
    horizontal=True
)

# Duration & Number of Clips
if mode != "Manual Mode":
    col1, col2 = st.columns(2)
    with col1:
        duration_choice = st.selectbox("Target Duration", ["15s", "30s", "60s", "90s", "120s", "Custom"])
        if duration_choice == "Custom":
            target_duration = st.number_input("Custom Duration (detik)", 5, 300, 45, 5)
        else:
            target_duration = int(duration_choice.replace("s", ""))
    with col2:
        number_of_clips = st.slider("Number of Clips", 1, 5, 3)
else:
    target_duration = 60
    number_of_clips = 1

# Quality
quality_choice = st.selectbox("Quality", ["360p", "480p", "720p", "1080p"], index=2)

# Other options
col_a, col_b = st.columns(2)
with col_a:
    tiktok_vertical = st.checkbox("📱 TikTok Vertical (9:16)", value=True)
    auto_tracking = st.checkbox("🎯 Auto Tracking", value=False)
with col_b:
    output_name = st.text_input("Output Prefix (opsional)", placeholder="clip_viral")
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
                st.success(f"✅ Added: {start_time} → {end_time} ({end-start}s)")
            else:
                st.error("End harus lebih besar dari Start")

        if st.session_state.get("manual_clips"):
            st.write(f"{len(st.session_state.manual_clips)} clips added:")
            for i, c in enumerate(st.session_state.manual_clips):
                st.write(f"{i+1}. {c['start']}s → {c['end']}s ({c['duration']}s)")
            if st.button("🗑️ Reset All"):
                st.session_state.manual_clips = []
                st.rerun()

# ==================== PROCESS ====================
if st.button("🚀 Start Processing", type="primary", use_container_width=True):
    if not url:
        st.error("Masukkan YouTube URL dulu!")
        st.stop()

    os.makedirs("downloads", exist_ok=True)

    # Clean old files
    for f in Path("downloads").glob("*"):
        try: f.unlink()
        except: pass

    # ── DOWNLOAD ──
    downloaded = "downloads/original.mp4"
    format_selector = build_format_selector(quality_choice)

    with st.status("📥 Downloading video...", expanded=True) as dl_status:
        st.write(f"Format: {quality_choice} — mencari stream terbaik...")
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "-f", format_selector,
            "-o", downloaded,
            "--merge-output-format", "mp4",
            "--no-check-certificate",
            "--extractor-args", "youtube:player_client=web,default",
        ]
        if COOKIES_FILE:
            cmd.extend(["--cookies", COOKIES_FILE])
        cmd.append(url)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            dl_status.update(label="❌ Download gagal", state="error")
            st.error(f"yt-dlp error:\n```\n{result.stderr[-800:]}\n```")
            st.stop()

        # Cari file hasil download
        candidates = list(Path("downloads").glob("original*"))
        if not candidates:
            candidates = list(Path("downloads").glob("*.mp4"))
        if not candidates:
            dl_status.update(label="❌ File tidak ditemukan", state="error")
            st.error("File download tidak ditemukan setelah yt-dlp selesai.")
            st.stop()

        downloaded = str(candidates[0])

        if not is_valid_video(downloaded):
            dl_status.update(label="❌ File corrupt", state="error")
            st.error("File yang didownload corrupt atau tidak valid.")
            st.stop()

        size_mb = os.path.getsize(downloaded) / 1024 / 1024
        w, h = get_video_resolution(downloaded)
        dl_status.update(
            label=f"✅ Download selesai — {w}x{h} ({size_mb:.1f} MB)",
            state="complete"
        )
        # Tampilkan resolusi aktual vs yang diminta
        requested_h = int(quality_choice.replace("p", ""))
        if h != requested_h:
            st.info(f"ℹ️ YouTube tidak punya stream {quality_choice} untuk video ini, "
                    f"didownload resolusi terdekat: {w}x{h}")

    # ── CLIPPING ──
    clips = []
    prefix = output_name.strip() if output_name.strip() else "clip"

    with st.status("✂️ Membuat clips...", expanded=True) as clip_status:

        if mode == "AI Suggested Moments":
            try:
                from analyzer import suggest_moments
                st.write("🧠 Analyzing video moments...")
                moments = suggest_moments(downloaded, max_moments=number_of_clips, variation=use_variation)
                for i, m in enumerate(moments):
                    out = f"downloads/{prefix}_{i+1}.mp4"
                    st.write(f"Clip {i+1}: {m['start']}s selama {target_duration}s")
                    ok, err = clip_video(downloaded, out, m["start"], target_duration)
                    if ok and is_valid_video(out):
                        clips.append(out)
                    else:
                        st.warning(f"Clip {i+1} gagal: {err[-200:]}")
            except ImportError:
                st.error("❌ `analyzer.py` tidak ditemukan!")
                st.stop()
            except Exception as e:
                st.error(f"❌ AI Analyzer error: {e}")
                st.stop()

        elif mode == "Auto Generate":
            for i in range(number_of_clips):
                start = i * (target_duration + 5)
                out = f"downloads/{prefix}_{i+1}.mp4"
                st.write(f"Clip {i+1}: {start}s → {start+target_duration}s")
                ok, err = clip_video(downloaded, out, start, target_duration)
                if ok and is_valid_video(out):
                    clips.append(out)
                else:
                    st.warning(f"Clip {i+1} gagal: {err[-200:]}")

        elif mode == "Manual Mode":
            manual = st.session_state.get("manual_clips", [])
            if not manual:
                clip_status.update(label="❌ Tidak ada manual clips", state="error")
                st.error("Tambahkan clips di Manual Mode dulu!")
                st.stop()
            for i, c in enumerate(manual):
                out = f"downloads/{prefix}_manual_{i+1}.mp4"
                st.write(f"Clip {i+1}: {c['start']}s → {c['end']}s ({c['duration']}s)")
                ok, err = clip_video(downloaded, out, c["start"], c["duration"])
                if ok and is_valid_video(out):
                    clips.append(out)
                else:
                    st.warning(f"Clip {i+1} gagal: {err[-200:]}")

        if not clips:
            clip_status.update(label="❌ Semua clips gagal", state="error")
            st.error("Tidak ada clip yang berhasil. Cek error di atas.")
            st.stop()

        clip_status.update(label=f"✅ {len(clips)} clips dibuat", state="complete")

    # ── TIKTOK VERTICAL + AUTO TRACKING ──
    if tiktok_vertical:
        with st.status("📱 Converting ke vertical...", expanded=True) as vtk_status:
            final = []
            for c in clips:
                out = c.replace(".mp4", "_tiktok.mp4")
                if auto_tracking:
                    st.write(f"🎯 Tracking + vertical: {Path(c).name}")
                    ok, err = convert_tracking(c, out)
                else:
                    st.write(f"📱 Vertical: {Path(c).name}")
                    ok, err = convert_vertical(c, out)

                if ok and is_valid_video(out):
                    final.append(out)
                    try: os.remove(c)
                    except: pass
                else:
                    st.warning(f"Convert gagal untuk {Path(c).name}, pakai versi horizontal.\n{err[-200:]}")
                    final.append(c)

            clips = final
            vtk_status.update(label=f"✅ Converted {len(clips)} clips", state="complete")

    # ── SAVE TO SESSION ──
    st.session_state.clips_data = []
    for clip in clips:
        if os.path.exists(clip):
            size_mb = round(os.path.getsize(clip) / 1024 / 1024, 1)
            w, h = get_video_resolution(clip)
            with open(clip, "rb") as f:
                st.session_state.clips_data.append({
                    "name": Path(clip).name,
                    "bytes": f.read(),
                    "size_mb": size_mb,
                    "resolution": f"{w}x{h}"
                })

    for f in Path("downloads").glob("*"):
        try: f.unlink()
        except: pass

    st.success(f"✅ Selesai! {len(st.session_state.clips_data)} clips siap didownload.")
    st.rerun()

# ==================== DISPLAY RESULTS ====================
if st.session_state.get("clips_data"):
    st.markdown("---")
    st.subheader("🎥 Preview & Download")

    st.markdown("""
    <style>
    [data-testid="stVideo"] {
        aspect-ratio: 9/16 !important;
        width: 100% !important;
        overflow: hidden !important;
        background: #000 !important;
        border-radius: 8px !important;
        margin-bottom: 4px !important;
    }
    [data-testid="stVideo"] video {
        width: 100% !important;
        height: 100% !important;
        object-fit: cover !important;
        border-radius: 8px !important;
    }
    [data-testid="column"] {
        padding: 0 4px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    data_list = st.session_state.clips_data
    ncols = 5
    cols = st.columns(ncols)

    for i, data in enumerate(data_list):
        with cols[i % ncols]:
            st.caption(f"{data['name']}")
            st.caption(f"📦 {data['size_mb']} MB · 🎬 {data.get('resolution', '-')}")

            if data['size_mb'] <= 100:
                st.video(data["bytes"], format="video/mp4")
            else:
                st.warning(f"⚠️ {data['size_mb']}MB — terlalu besar untuk preview")

            st.download_button(
                label=f"⬇️ Download {i+1}",
                data=data["bytes"],
                file_name=data["name"],
                mime="video/mp4",
                key=f"dl_{i}",
                use_container_width=True
            )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Clear Results"):
        del st.session_state["clips_data"]
        st.rerun()