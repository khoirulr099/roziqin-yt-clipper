import os
import subprocess
import json
import random
from pathlib import Path

def suggest_moments(video_path, max_moments=5, min_duration=8, variation=False):
    """
    Analisis video menggunakan Scene Change + Audio Energy + Fallback sampling.
    Jika variation=True, akan menambahkan sedikit offset acak (±3 sampai ±8 detik)
    agar hasilnya berbeda setiap generate.
    """
    if not os.path.exists(video_path):
        return []

    suggestions = []

    # === 1. Scene Change Detection ===
    print("🔍 Analyzing scenes...")
    scene_cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", "select='gt(scene,0.15)',showinfo",
        "-f", "null", "-"
    ]

    result = subprocess.run(scene_cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    output = result.stderr

    timestamps = []
    for line in output.splitlines():
        if "pts_time:" in line:
            try:
                time_str = line.split("pts_time:")[1].split()[0]
                timestamps.append(float(time_str))
            except:
                pass

    # === 2. Audio Energy Analysis ===
    print("🔊 Analyzing audio energy...")
    audio_cmd = [
        "ffmpeg", "-i", video_path,
        "-af", "silencedetect=noise=0.02:d=0.5",
        "-f", "null", "-"
    ]

    audio_result = subprocess.run(audio_cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    audio_output = audio_result.stderr

    non_silent = []
    for line in audio_output.splitlines():
        if "silence_end" in line:
            try:
                time_str = line.split("silence_end:")[1].split()[0]
                non_silent.append(float(time_str))
            except:
                pass

    # === 3. Gabungkan Scene + Audio Energy ===
    for i in range(len(timestamps) - 1):
        start = timestamps[i]
        end = timestamps[i + 1]
        duration = end - start

        if duration >= min_duration:
            score = 0.6
            for ns in non_silent:
                if start <= ns <= end:
                    score = 0.9
                    break

            suggestions.append({
                "start": round(start, 1),
                "end": round(end, 1),
                "duration": round(duration, 1),
                "type": "scene_change",
                "score": score
            })

    # === 4. Fallback sampling ===
    if len(suggestions) < max_moments * 2:
        print("⚠️ Scene change sedikit, menambahkan sampling merata...")
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", video_path],
                capture_output=True, text=True
            )
            total_duration = float(probe.stdout.strip())

            step = total_duration / (max_moments + 1)
            for i in range(max_moments):
                start = step * (i + 1)
                suggestions.append({
                    "start": round(start, 1),
                    "end": round(start + min_duration, 1),
                    "duration": min_duration,
                    "type": "fallback",
                    "score": 0.5
                })
        except:
            pass

    # Sort berdasarkan skor tertinggi
    suggestions = sorted(suggestions, key=lambda x: x["score"], reverse=True)[:max_moments]

    # === VARIATION MODE ===
    if variation and suggestions:
        print("🔄 Menambahkan variasi posisi scene...")
        varied = []
        for s in suggestions:
            offset = random.uniform(-8, 8)  # ±8 detik
            new_start = max(0, s["start"] + offset)
            new_end = new_start + s["duration"]
            varied.append({
                "start": round(new_start, 1),
                "end": round(new_end, 1),
                "duration": s["duration"],
                "type": s["type"] + "_varied",
                "score": s["score"]
            })
        suggestions = varied

    return suggestions


def generate_ass_subtitle(
    video_path: str,
    output_ass: str,
    language: str = "id",
    font_size: int = 28,
    subtitle_color: str = "Putih",
    position: str = "Bawah Tengah",
    highlight_color: str = "Kuning",
    model_name: str = "base"
) -> str:
    """
    Generate subtitle .ass dengan styling yang mengikuti pilihan user.
    """
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, info = model.transcribe(video_path, language=language, beam_size=5)

    color_map = {
        "Putih": "&H00FFFFFF&",
        "Kuning": "&H0000FFFF&",
        "Cyan": "&H00FFFF00&",
        "Hijau": "&H0000FF00&"
    }

    primary_color = color_map.get(subtitle_color, "&H00FFFFFF&")
    highlight = color_map.get(highlight_color, "&H0000FFFF&")

    alignment_map = {
        "Bawah Tengah": 2,
        "Tengah": 5,
        "Atas": 8
    }
    alignment = alignment_map.get(position, 2)

    ass_header = f"""[Script Info]
Title: TikTok Subtitle
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TikTok,Arial,{font_size},{primary_color},&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,2,{alignment},10,10,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    for segment in segments:
        start = segment.start
        end = segment.end
        text = segment.text.strip()

        def format_time(t):
            h = int(t // 3600)
            m = int((t % 3600) // 60)
            s = int(t % 60)
            cs = int((t - int(t)) * 100)
            return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

        start_time = format_time(start)
        end_time = format_time(end)

        words = text.split()
        if words:
            highlighted = f"{{\\c{highlight}}}{words[0]}{{\\c{primary_color}}} {' '.join(words[1:])}"
        else:
            highlighted = text

        event = f"Dialogue: 0,{start_time},{end_time},TikTok,,0,0,0,,{highlighted}"
        events.append(event)

    with open(output_ass, "w", encoding="utf-8") as f:
        f.write(ass_header)
        f.write("\n".join(events))

    print(f"✅ ASS Subtitle berhasil dibuat: {output_ass}")
    return output_ass


if __name__ == "__main__":
    video = "downloads/test.mp4"
    if os.path.exists(video):
        moments = suggest_moments(video)
        print(json.dumps(moments, indent=2))
    else:
        print("Video tidak ditemukan untuk testing.")