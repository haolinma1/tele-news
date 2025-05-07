"""
Watch chosen Telegram channels/groups and forward an alert
whenever a message contains certain keywords.
"""
import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient, events

# ──────────────────────────────────────────────────────
# 1) Config via .env
# ──────────────────────────────────────────────────────
load_dotenv()                       # <-- IMPORTANT!

API_ID   = int(os.getenv("TELE_ID"))
API_HASH = os.getenv("TELE_HASH")

# (optional) second client just for sending alerts
BOT_TOKEN = os.getenv("ALERT_BOT_TOKEN")   # leave blank if you’ll reuse user client
ALERT_CHAT = os.getenv("ALERT_CHAT", "me") # “me” = Saved Messages

# Channels / groups you want to monitor
# Use usernames or numeric IDs (NOT the t.me URLs)
WATCHED_CHATS = [
    "hyperliquid_announcements",
    "Bybit_Announcements",
    "binance_announcements",
    "Bitget_Announcements",
    "OKXAnnouncements"
]

# Keywords to trigger an alert (case‑insensitive)
KEYWORDS = [
    "delist",
    "delisting",
    "remove trading",
    "下架", "退市",
]

# ──────────────────────────────────────────────────────
# 2) Create listening client (user account)
# ──────────────────────────────────────────────────────
listen_client = TelegramClient("listener_session", API_ID, API_HASH)

# ──────────────────────────────────────────────────────
# 3) Optional: separate client for alerts (bot account)
#    If no BOT_TOKEN is given we’ll just send from the
#    same user session to Saved Messages (or any chat ID).
# ──────────────────────────────────────────────────────
alert_client = (
    TelegramClient("alert_bot_session", API_ID, API_HASH)
    if not BOT_TOKEN               # reuse user account
    else TelegramClient("alert_bot_session", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
)

# ──────────────────────────────────────────────────────
# 4) Handler: fire only for the channels we watch
# ──────────────────────────────────────────────────────
@listen_client.on(events.NewMessage(chats=WATCHED_CHATS))
async def announcement_handler(event: events.NewMessage.Event):
    text = event.raw_text.lower()

    if any(kw in text for kw in KEYWORDS):
        preview = (event.raw_text[:400] + "…") if len(event.raw_text) > 400 else event.raw_text
        alert = (
            f"🛑 **Keyword hit in {event.chat.title or 'Unknown'}**\n\n"
            f"```{preview}```\n"
            f"[Jump to message]({event.message.link})"
            if event.is_channel else preview
        )

        # Send via chosen alert client
        await alert_client.send_message(entity=ALERT_CHAT, message=alert, link_preview=False)
        print("ALERT sent:", preview.replace("\n", " ")[:120])
    else:
        print("No match:", text.replace("\n", " ")[:80])


# ──────────────────────────────────────────────────────
# 5) Main entry
# ──────────────────────────────────────────────────────
async def main():
    await listen_client.start()          # user login (first run will ask phone / code)
    if alert_client is not listen_client:
        await alert_client.start()       # starts bot session or second user session

    print("🔍 Monitoring announcement channels …")
    await asyncio.gather(
        listen_client.run_until_disconnected(),
        # keep alert_client alive too (noop loop) if it’s different
        alert_client.run_until_disconnected() if alert_client is not listen_client else asyncio.Future(),
    )

if __name__ == "__main__":
    asyncio.run(main())

