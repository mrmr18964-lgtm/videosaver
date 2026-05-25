import os
import asyncio
import tempfile
import logging
from pathlib import Path

from telegram import Update, Message
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode
import yt_dlp

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Config ─────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ["BOT_TOKEN"]       # required env var
MAX_FILE_MB = int(os.environ.get("MAX_FILE_MB", "50"))   # Telegram limit = 50 MB
DOWNLOAD_DIR = Path(tempfile.gettempdir()) / "videobot"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Supported domains (yt-dlp handles hundreds more automatically)
SUPPORTED_HINT = (
    "YouTube, Instagram, TikTok, Twitter/X, Facebook, "
    "Vimeo, Dailymotion va boshqa ko'plab saytlar"
)

# ─── yt-dlp options ─────────────────────────────────────────────────────────
def build_ydl_opts(out_tmpl: str) -> dict:
    return {
        "outtmpl": out_tmpl,
        "format": "18/22/bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 60,
        "retries": 5,
        "fragment_retries": 5,
        "extractor_retries": 5,
        "ignoreerrors": False,
        "postprocessors": [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4",
        }],
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────
async def send_status(msg: Message, text: str) -> Message:
    """Edit status message or send a new one."""
    return await msg.reply_text(text, parse_mode=ParseMode.HTML)


def human_size(n_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} TB"


# ─── Download logic (runs in thread pool) ────────────────────────────────────
def download_video(url: str, out_tmpl: str) -> dict:
    """Blocking download; returns yt-dlp info dict."""
    opts = build_ydl_opts(out_tmpl)
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info


# ─── Handlers ────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Video Yuklovchi Bot</b>ga xush kelibsiz!\n\n"
        f"🔗 Menga video havolasini yuboring — men uni yuklab, to'g'ridan-to'g'ri "
        f"video sifatida qaytaraman.\n\n"
        f"<b>Qo'llab-quvvatlanadi:</b> {SUPPORTED_HINT}",
        parse_mode=ParseMode.HTML,
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>Foydalanish:</b>\n\n"
        "1️⃣ Video havolasini (URL) yuboring\n"
        "2️⃣ Bot yuklab, sizga video yuboradi\n\n"
        f"⚠️ Maksimal hajm: <b>{MAX_FILE_MB} MB</b>\n"
        f"📌 Qo'llab-quvvatlanadilar: {SUPPORTED_HINT}",
        parse_mode=ParseMode.HTML,
    )


async def handle_url(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.effective_chat.id
    user = update.effective_user
    logger.info("User %s (%s) sent URL: %s", user.id, user.username, url)

    # ── 1. Status message ──────────────────────────────────────────────────
    status = await update.message.reply_text(
        "⏳ <b>Yuklanmoqda…</b>\nIltimos kuting.",
        parse_mode=ParseMode.HTML,
    )

    # ── 2. Temp output template ───────────────────────────────────────────
    uid = update.message.message_id
    out_tmpl = str(DOWNLOAD_DIR / f"{chat_id}_{uid}.%(ext)s")

    # ── 3. Download in executor ───────────────────────────────────────────
    loop = asyncio.get_event_loop()
    try:
        info = await loop.run_in_executor(None, download_video, url, out_tmpl)
    except yt_dlp.utils.DownloadError as e:
        err_msg = str(e).splitlines()[-1]
        logger.warning("DownloadError for %s: %s", url, err_msg)
        await status.edit_text(
            f"❌ <b>Yuklab bo'lmadi:</b>\n<code>{err_msg}</code>\n\n"
            "URL to'g'ri ekanligini tekshiring yoki boshqa havola yuboring.",
            parse_mode=ParseMode.HTML,
        )
        return
    except Exception as e:
        logger.exception("Unexpected error for %s", url)
        await status.edit_text(
            "❌ Kutilmagan xato yuz berdi. Keyinroq urinib ko'ring.",
            parse_mode=ParseMode.HTML,
        )
        return

    # ── 4. Find downloaded file ────────────────────────────────────────────
    # yt-dlp writes the final filename; find it
    video_path: Path | None = None
    for f in DOWNLOAD_DIR.glob(f"{chat_id}_{uid}.*"):
        if f.suffix.lower() in (".mp4", ".mkv", ".webm", ".mov", ".avi"):
            video_path = f
            break

    if video_path is None or not video_path.exists():
        await status.edit_text(
            "❌ Fayl topilmadi. Ehtimol format qo'llab-quvvatlanmaydi.",
            parse_mode=ParseMode.HTML,
        )
        return

    file_size = video_path.stat().st_size
    if file_size > MAX_FILE_MB * 1024 * 1024:
        video_path.unlink(missing_ok=True)
        await status.edit_text(
            f"⚠️ Video hajmi <b>{human_size(file_size)}</b> — "
            f"bu Telegram chegarasi ({MAX_FILE_MB} MB) dan katta.\n"
            "Kichikroq video yuboring.",
            parse_mode=ParseMode.HTML,
        )
        return

    # ── 5. Build caption ───────────────────────────────────────────────────
    title = info.get("title", "Video")[:200]
    duration = info.get("duration")
    dur_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "—"
    caption = (
        f"🎬 <b>{title}</b>\n"
        f"⏱ {dur_str}  •  📦 {human_size(file_size)}"
    )

    # ── 6. Send video ──────────────────────────────────────────────────────
    await status.edit_text("📤 <b>Yuborilmoqda…</b>", parse_mode=ParseMode.HTML)
    try:
        with open(video_path, "rb") as vf:
            await ctx.bot.send_video(
                chat_id=chat_id,
                video=vf,
                caption=caption,
                parse_mode=ParseMode.HTML,
                supports_streaming=True,
                read_timeout=120,
                write_timeout=120,
                connect_timeout=30,
            )
        await status.delete()
        logger.info("Sent %s to %s", video_path.name, chat_id)
    except Exception as e:
        logger.exception("Failed to send video to %s", chat_id)
        await status.edit_text(
            "❌ Videoni yuborishda xato yuz berdi. Qayta urinib ko'ring.",
            parse_mode=ParseMode.HTML,
        )
    finally:
        video_path.unlink(missing_ok=True)


async def handle_non_url(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔗 Iltimos, faqat video <b>havolasini</b> yuboring.\n"
        "Masalan: <code>https://youtube.com/watch?v=…</code>",
        parse_mode=ParseMode.HTML,
    )


# ─── URL filter ──────────────────────────────────────────────────────────────
def is_url(text: str) -> bool:
    t = (text or "").strip().lower()
    return t.startswith("http://") or t.startswith("https://")


URL_FILTER = filters.TEXT & filters.Regex(r"https?://\S+")
NON_URL_FILTER = filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"https?://\S+")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(120)
        .write_timeout(120)
        .connect_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(URL_FILTER, handle_url))
    app.add_handler(MessageHandler(NON_URL_FILTER, handle_non_url))

    logger.info("Bot starting…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()