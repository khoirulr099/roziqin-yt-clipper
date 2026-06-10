# YouTube Auto Clip

English Version

YouTube Auto Clip is a simple tool to cut videos from YouTube. You can choose to let it cut automatically, use AI to find good moments, or cut manually yourself. It also supports automatic subtitles and vertical format for TikTok/Reels.

## Features

- Auto Generate (1-5 clips): Automatically creates clips from different parts of the video.
- AI Suggested Moments (1-5 clips): Detects interesting scenes and audio energy to suggest good moments.
- Manual Mode: You control the start and end time for each clip. You can add multiple clips.
- Number of Clips: Choose how many clips you want (1 to 5).
- Target Clip Duration: Set duration to 30s, 60s, 90s, 120s, or custom.
- Auto Subtitle: Generate and burn subtitles using Whisper (tiny, base, small, medium).
- Vertical Format (9:16): Automatically converts clips to TikTok/Reels format.
- Auto Tracking (optional): Uses motion tracking from auto-editor (works best for 1-2 people).
- Auto Delete: All original files are automatically deleted after preview.

## Installation (Local)

1. Make sure you have Python 3.10+ and FFmpeg installed.
2. Clone or download this repository.
3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Run the app:

```bash
python3 -m streamlit run app.py
```

5. Open your browser at http://localhost:8501

---

Versi Bahasa Indonesia

YouTube Auto Clip adalah tool sederhana untuk memotong video dari YouTube. Kamu bisa memilih mode otomatis, pakai AI untuk cari momen bagus, atau potong secara manual. Bisa juga tambah subtitle otomatis dan ubah ke format vertikal untuk TikTok/Reels.

## Fitur

- Auto Generate (1-5 klip): Otomatis memotong video dari beberapa bagian berbeda.
- AI Suggested Moments (1-5 klip): Mendeteksi scene menarik dan energi audio untuk sarankan momen bagus.
- Manual Mode: Kamu yang atur sendiri mulai dan akhir tiap klip. Bisa tambah beberapa klip.
- Jumlah Klip: Bisa diatur dari 1 sampai 5 klip.
- Durasi Klip: Pilih 30 detik, 60 detik, 90 detik, 120 detik, atau custom.
- Subtitle Otomatis: Generate dan bakar subtitle pakai Whisper (tiny, base, small, medium).
- Format Vertikal (9:16): Otomatis ubah ke format TikTok/Reels.
- Auto Tracking (opsional): Motion tracking pakai auto-editor (cocok untuk 1-2 orang).
- Auto Delete: Semua file asli otomatis dihapus setelah preview muncul.

## Instalasi (Lokal)

1. Pastikan sudah install Python 3.10+ dan FFmpeg.
2. Clone atau download repository ini.
3. Install semua package yang dibutuhkan:

```bash
pip install -r requirements.txt
```

4. Jalankan aplikasinya:

```bash
python3 -m streamlit run app.py
```

5. Buka browser di http://localhost:8501

---

## Catatan Penting

- FFmpeg harus sudah terinstall.
- Untuk penggunaan lokal, buat file .env berisi TELEGRAM_TOKEN dan TELEGRAM_CHAT_ID kalau mau kirim ke Telegram.
- Folder downloads akan otomatis dibersihkan setelah preview muncul.

Created by Roziqin