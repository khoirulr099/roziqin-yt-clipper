import os
import subprocess
from pathlib import Path
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# States
MODE, URL, NUM_CLIPS, DURATION, CUSTOM_DURATION, QUALITY, TIKTOK, TRACKING, CONFIRM = range(9)

QUALITY_MAP = {
    "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Selamat datang di Roziqin YouTube Clipper!**\n\n"
        "Bot ini bisa membantu kamu memotong video YouTube secara otomatis.\n\n"
        "Gunakan perintah /clip untuk mulai membuat clip."
    )
    return ConversationHandler.END

async def start_clip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Kirim URL YouTube yang ingin di-clip:")
    return URL

async def get_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["url"] = update.message.text
    keyboard = [["Auto Generate", "AI Suggested"]]
    await update.message.reply_text(
        "Pilih mode clipping:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return MODE

async def get_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = update.message.text
    await update.message.reply_text("Berapa clip yang ingin dibuat? (1-5)")
    return NUM_CLIPS

async def get_num_clips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        num = int(update.message.text)
        if 1 <= num <= 5:
            context.user_data["num_clips"] = num
            keyboard = [["30", "60", "90", "120", "Custom"]]
            await update.message.reply_text(
                "Pilih durasi per clip (detik):",
                reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
            return DURATION
        else:
            await update.message.reply_text("Masukkan angka antara 1-5.")
            return NUM_CLIPS
    except:
        await update.message.reply_text("Masukkan angka yang valid.")
        return NUM_CLIPS

async def get_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "Custom":
        await update.message.reply_text("Masukkan durasi custom (detik), contoh: 45")
        return CUSTOM_DURATION

    try:
        duration = int(text)
        if 5 <= duration <= 300:
            context.user_data["duration"] = duration
            keyboard = [["360p", "480p", "720p", "1080p"]]
            await update.message.reply_text(
                "Pilih kualitas video:",
                reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
            return QUALITY
        else:
            await update.message.reply_text("Durasi harus antara 5-300 detik.")
            return DURATION
    except:
        await update.message.reply_text("Pilih dari tombol atau ketik angka yang valid.")
        return DURATION

async def get_custom_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        duration = int(update.message.text.strip())
        if 5 <= duration <= 300:
            context.user_data["duration"] = duration
            keyboard = [["360p", "480p", "720p", "1080p"]]
            await update.message.reply_text(
                "Pilih kualitas video:",
                reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
            return QUALITY
        else:
            await update.message.reply_text("Durasi harus antara 5-300 detik.")
            return CUSTOM_DURATION
    except:
        await update.message.reply_text("Masukkan angka yang valid (contoh: 45).")
        return CUSTOM_DURATION

async def get_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quality = update.message.text.strip()
    if quality in QUALITY_MAP:
        context.user_data["quality"] = quality
        keyboard = [["Ya", "Tidak"]]
        await update.message.reply_text(
            "Ingin format TikTok Vertical (9:16)?",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return TIKTOK
    else:
        await update.message.reply_text("Pilih kualitas dari tombol yang tersedia.")
        return QUALITY

async def get_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tiktok"] = update.message.text == "Ya"
    keyboard = [["Ya", "Tidak"]]
    await update.message.reply_text(
        "Aktifkan Auto Tracking?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return TRACKING

async def get_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tracking"] = update.message.text == "Ya"
    keyboard = [["Ya", "Tidak"]]
    await update.message.reply_text(
        "Semua sudah benar? Tekan tombol untuk mulai proses:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CONFIRM

async def confirm_and_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text != "Ya":
        await update.message.reply_text("Proses dibatalkan.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    data = context.user_data
    await update.message.reply_text("⏳ Sedang memproses... Mohon tunggu.")

    url = data["url"]
    num_clips = data["num_clips"]
    duration = data["duration"]
    quality = data.get("quality", "720p")
    format_selector = QUALITY_MAP.get(quality, QUALITY_MAP["720p"])
    tiktok = data["tiktok"]

    os.makedirs("downloads", exist_ok=True)

    # Progress
    await update.message.reply_text(f"📥 Downloading video ({quality})...")
    ydl_opts = {
        "format": format_selector,
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "merge_output_format": "mp4",
    }
    try:
        import yt_dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)
    except Exception as e:
        await update.message.reply_text(f"❌ Download gagal: {e}")
        return ConversationHandler.END

    clips = []

    await update.message.reply_text(f"✂️ Membuat {num_clips} clip...")

    if data["mode"] == "AI Suggested":
        from analyzer import suggest_moments
        moments = suggest_moments(downloaded_file, max_moments=num_clips)
        for i, moment in enumerate(moments):
            output = f"downloads/ai_clip_{i+1}.mp4"
            cmd = ["ffmpeg", "-y", "-ss", str(moment["start"]), "-i", downloaded_file, "-t", str(duration), "-c", "copy", output]
            subprocess.run(cmd, capture_output=True)
            if os.path.exists(output):
                clips.append(output)
    else:
        for i in range(num_clips):
            start = i * (duration + 10)
            output = f"downloads/clip_{i+1}.mp4"
            cmd = ["ffmpeg", "-y", "-ss", str(start), "-i", downloaded_file, "-t", str(duration), "-c", "copy", output]
            subprocess.run(cmd, capture_output=True)
            if os.path.exists(output):
                clips.append(output)

    if tiktok and clips:
        final = []
        for c in clips:
            out = c.replace(".mp4", "_tiktok.mp4")
            cmd = ["ffmpeg", "-y", "-i", c, "-vf", "scale=-1:1920,crop=1080:1920", "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "aac", "-b:a", "128k", out]
            subprocess.run(cmd, capture_output=True)
            if os.path.exists(out):
                final.append(out)
        clips = final

    await update.message.reply_text("📤 Mengirim clip ke Telegram...")

    # Send videos - only show error if it really fails
    success_count = 0
    for clip in clips:
        try:
            await update.message.reply_video(video=clip, caption=Path(clip).name)
            success_count += 1
        except Exception as e:
            # Only show real errors, not timeout
            if "timeout" not in str(e).lower():
                await update.message.reply_text(f"❌ Gagal mengirim {Path(clip).name}")

    # Auto delete all files
    for file in os.listdir("downloads"):
        try:
            os.remove(os.path.join("downloads", file))
        except:
            pass

    if success_count > 0:
        await update.message.reply_text(
            f"✅ Selesai! {success_count} clip berhasil dikirim dan file dihapus otomatis.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text("❌ Tidak ada clip yang berhasil dikirim.", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Proses dibatalkan.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN tidak ditemukan!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("clip", start_clip)],
        states={
            URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_url)],
            MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_mode)],
            NUM_CLIPS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_num_clips)],
            DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_duration)],
            CUSTOM_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_custom_duration)],
            QUALITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quality)],
            TIKTOK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tiktok)],
            TRACKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tracking)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_and_process)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    print("🤖 Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()