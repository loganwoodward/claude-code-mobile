"""
Claude Code Mobile Bridge
Connects your phone (Telegram) to your Claude Code session via files.
No API required — messages flow through the local file system.

Usage:
  1. Set your bot token: set TELEGRAM_BOT_TOKEN=your_token_here
  2. Run: python bridge.py
  Or just use start.bat
"""

import os
import sys
import time
import asyncio
import logging
import subprocess
import json
from pathlib import Path

logging.basicConfig(level=logging.WARNING)

try:
    from telegram import Update
    from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
except ImportError:
    print("\n  Missing dependency. Run:")
    print('  pip install "python-telegram-bot[job-queue]"\n')
    sys.exit(1)

# === CONFIG ===
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
BASE_DIR = Path(__file__).parent
INCOMING = BASE_DIR / "incoming"
OUTGOING = BASE_DIR / "outgoing"
PUSH = BASE_DIR / "push"
USER_FILE = BASE_DIR / "authorized_user.json"
SENDKEYS_SCRIPT = BASE_DIR / "sendkeys.ps1"
RESPONSE_TIMEOUT = 180  # seconds
RETRY_INTERVAL = 30     # seconds between Send-Keys retries

for d in [INCOMING, OUTGOING, PUSH]:
    d.mkdir(parents=True, exist_ok=True)

ALLOWED_USER = None
PROCESSED_IDS = set()


def load_user():
    global ALLOWED_USER
    if USER_FILE.exists():
        ALLOWED_USER = json.loads(USER_FILE.read_text()).get("user_id")


def save_user(uid):
    global ALLOWED_USER
    ALLOWED_USER = uid
    USER_FILE.write_text(json.dumps({"user_id": uid}))


def send_keys(message):
    """Type a message into the active Claude Code window via PowerShell."""
    if not SENDKEYS_SCRIPT.exists():
        print("[SENDKEYS] sendkeys.ps1 not found — see README for setup")
        return False
    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File",
             str(SENDKEYS_SCRIPT), "-Message", message],
            capture_output=True, text=True, timeout=15
        )
        return "SENT" in result.stdout.upper()
    except Exception as e:
        print(f"[SENDKEYS] Error: {e}")
        return False


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ALLOWED_USER
    user = update.effective_user

    if ALLOWED_USER is None:
        save_user(user.id)
        print(f"  Authorized user: {user.first_name} ({user.id})")
    elif user.id != ALLOWED_USER:
        return

    text = update.message.text
    if not text:
        return

    tg_id = update.message.message_id
    if tg_id in PROCESSED_IDS:
        return
    PROCESSED_IDS.add(tg_id)

    msg_id = int(time.time() * 1000)
    (INCOMING / f"{msg_id}.txt").write_text(text, encoding="utf-8")
    print(f"[IN] {text[:80].encode('ascii', 'replace').decode()}")

    # Send-Keys with conditional retry (only if first attempt failed)
    prompt = f"[TELEGRAM:{msg_id}] Message: {text}"
    sent = send_keys(prompt)
    if not sent:
        print("[WARN] Send-Keys failed on first attempt — will retry during wait")

    # Wait for response, retrying Send-Keys ONLY if the first attempt failed.
    # Unconditional retry would spam duplicate messages into the Claude window
    # whenever the session takes >RETRY_INTERVAL to respond, which is normal
    # for thinking-heavy replies.
    response = None
    target = OUTGOING / f"{msg_id}.txt"
    start = time.time()
    last_retry = start
    retry_count = 0
    max_retries = 2
    while time.time() - start < RESPONSE_TIMEOUT:
        if target.exists():
            await asyncio.sleep(0.5)
            content = target.read_text(encoding="utf-8").strip()
            if content:
                target.unlink()
                response = content
                break
        # Retry only if the original send failed and we're under the retry cap
        if not sent and retry_count < max_retries and time.time() - last_retry >= RETRY_INTERVAL:
            retry_count += 1
            print(f"[RETRY {retry_count}/{max_retries}] Re-sending via Send-Keys...")
            retry_sent = send_keys(prompt)
            if retry_sent:
                sent = True  # success — stop retrying
            last_retry = time.time()
        await asyncio.sleep(1)

    if response:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(response[i:i+4096])
        print(f"[OUT] {response[:80].encode('ascii', 'replace').decode()}")
    else:
        await update.message.reply_text("(Session is away or busy — message queued)")
        print(f"[TIMEOUT] No response within {RESPONSE_TIMEOUT}s")
        alert = (
            f"[TELEGRAM ALERT] Message went unanswered for {RESPONSE_TIMEOUT}s. "
            f"Message was: {text[:80]}. "
            f"Check if session is stuck. Use push/ folder to notify the user."
        )
        send_keys(alert)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ALLOWED_USER
    user = update.effective_user
    if ALLOWED_USER and user.id != ALLOWED_USER:
        return

    msg_id = int(time.time() * 1000)
    photo = update.message.photo[-1]
    caption = update.message.caption or ""

    img_dir = INCOMING / "images"
    img_dir.mkdir(exist_ok=True)
    img_path = img_dir / f"{msg_id}.jpg"

    photo_file = await photo.get_file()
    await photo_file.download_to_drive(str(img_path))
    print(f"[PHOTO] Saved to {img_path}")

    prompt = f"[TELEGRAM:{msg_id}] Photo received at: {img_path} Caption: {caption}"
    send_keys(prompt)

    response = None
    target = OUTGOING / f"{msg_id}.txt"
    start = time.time()
    last_retry = start
    while time.time() - start < RESPONSE_TIMEOUT:
        if target.exists():
            await asyncio.sleep(0.5)
            content = target.read_text(encoding="utf-8").strip()
            if content:
                target.unlink()
                response = content
                break
        if time.time() - last_retry >= RETRY_INTERVAL:
            send_keys(prompt)
            last_retry = time.time()
        await asyncio.sleep(1)

    if response:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(response[i:i+4096])
    else:
        await update.message.reply_text("(Got the photo — session will process when available)")


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Claude Code Mobile Bridge\n\n"
        "Text me and your message goes straight to your Claude Code session.\n"
        "Your AI responds through me. No API required."
    )


def main():
    if not BOT_TOKEN:
        print("\n  Claude Code Mobile Bridge")
        print("  =========================")
        print("  Set your bot token first:\n")
        print("    set TELEGRAM_BOT_TOKEN=your_token_here")
        print("    python bridge.py\n")
        print("  Or paste the token into start.bat")
        sys.exit(1)

    load_user()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Push watcher — lets Claude send messages to the user proactively
    async def push_watcher(context):
        if not ALLOWED_USER:
            return
        try:
            for f in sorted(PUSH.glob("*.txt")):
                content = f.read_text(encoding="utf-8").strip()
                if content:
                    for i in range(0, len(content), 4096):
                        await context.bot.send_message(
                            chat_id=ALLOWED_USER, text=content[i:i+4096])
                    print(f"[PUSH] {content[:60].encode('ascii', 'replace').decode()}")
                f.unlink()
        except Exception as e:
            print(f"[PUSH] Error: {e}")

    app.job_queue.run_repeating(push_watcher, interval=5, first=5)

    print()
    print("  ==============================")
    print("  Claude Code Mobile Bridge")
    print("  ==============================")
    print(f"  Timeout: {RESPONSE_TIMEOUT}s")
    print(f"  Retry:   every {RETRY_INTERVAL}s")
    print("  Waiting for messages...")
    print()

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
