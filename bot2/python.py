import os
import re
import logging
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import time

# Logging sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram bot tokeni
TOKEN = "8334033803:AAHst4drgbbhyCzfO9fbsqup_mkKLic7dzU"   # <-- bu yerga o'z tokeningizni yozing

# YouTube URLni tekshirish uchun regex
YOUTUBE_REGEX = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! YouTube video yoki shorts linkini yuboring, men uni sizga 720p sifatida yuboraman. ✅"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    match = re.match(YOUTUBE_REGEX, text)

    if not match:
        if not text.startswith("/"):
            await update.message.reply_text(
                "⚠️ Iltimos, to‘g‘ri YouTube video yoki shorts linkini yuboring."
            )
        return

    video_id = match.group(1)
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        await update.message.reply_text("🔎 Video ma'lumotlari olinmoqda...")

        # Faqat 720p yoki past sifat yuklaymiz (audio bilan)
        ydl_opts = {
            "format": "best[height<=720][ext=mp4]/best[height<=720]",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "outtmpl": f"temp_{video_id}.%(ext)s",
        }

        buffer = BytesIO()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            title = info.get("title", "Video")
            filename = ydl.prepare_filename(info)

            # Faylni RAM (BytesIO) ga yozamiz
            with open(filename, "rb") as f:
                buffer.write(f.read())

        buffer.seek(0)
        buffer.name = f"{video_id}.mp4"

        size = buffer.getbuffer().nbytes
        if size > 50 * 1024 * 1024:
            await update.message.reply_text(
                f"⚠️ Video hajmi 50 MB dan katta. ({size / (1024*1024):.2f} MB)"
            )
            os.remove(filename)
            return

        await update.message.reply_video(
            video=buffer,
            caption=f"{title}\n\n📌 Bot orqali yuklandi 👉 t.me/Zufarbekjumayev77_bot",
            supports_streaming=True
        )

        # Diskda vaqtinchalik faylni o‘chirib tashlaymiz
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        logger.error(f"Xato: {e}")
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")


def run_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    while True:
        try:
            run_bot()
        except Exception as e:
            logger.error(f"Bot to‘xtadi! Xato: {e}")
            logger.info("♻️ 5 daqiqadan keyin qayta ishga tushadi...")
            time.sleep(300)  # 300 soniya = 5 minut
