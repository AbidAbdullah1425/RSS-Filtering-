import feedparser
import asyncio
import logging
from bot import Bot
from pyrogram import filters
from config import OWNER_ID, DB_URI, DB_NAME
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB Setup
client = AsyncIOMotorClient(DB_URI)
db = client[DB_NAME]
posts_collection = db.posts

# Logger setup
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Variables
RSS_URL = "https://subsplease.org/rss/?t&r=sd"
CHANNEL_ID = -1002322411485
CHECK_INTERVAL = 60  # seconds
is_running = False

async def fetch_and_send_rss():
    while is_running:
        logger.info("Fetching RSS feed...")
        feed = feedparser.parse(RSS_URL)
        if feed.entries:
            new_entries = []
            logger.info("Found %d entries in the RSS feed.", len(feed.entries))

            # Collect new entries in down-to-top order (oldest to newest)
            for entry in reversed(feed.entries):
                if not await posts_collection.find_one({"_id": entry.id}):
                    new_entries.append(entry)

            if new_entries:
                logger.info("Found %d new entries to process.", len(new_entries))

            for entry in new_entries:
                title = entry.title
                torrent_link = entry.link
                message = f"{title}\n\n`{torrent_link}` #torrent"

                # Send to private channel
                try:
                    await Bot.send_message(chat_id=CHANNEL_ID, text=message)
                    logger.info("Successfully sent post: %s", title)

                    # Save the entry to the database
                    await posts_collection.insert_one({"_id": entry.id, "title": entry.title, "link": entry.link})
                except Exception as e:
                    logger.error("Failed to send post: %s. Error: %s", title, str(e))
            
            if not new_entries:
                logger.info("No new entries to process.")

        else:
            logger.warning("No entries found in the RSS feed.")

        await asyncio.sleep(CHECK_INTERVAL)

# Start command
@Bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_rss(client, message):
    global is_running

    if not is_running:
        is_running = True
        logger.info("Received start command from OWNER_ID.")
        await message.reply_text("Started monitoring RSS feed.")
        await fetch_and_send_rss()
    else:
        logger.info("Start command received, but monitoring is already running.")
        await message.reply_text("RSS feed monitoring is already running.")

# Stop command
@Bot.on_message(filters.command("stop") & filters.user(OWNER_ID))
async def stop_rss(client, message):
    global is_running

    if is_running:
        is_running = False
        logger.info("Received stop command from OWNER_ID. Stopping monitoring.")
        await message.reply_text("Stopped monitoring RSS feed.")
    else:
        logger.info("Stop command received, but monitoring was not running.")
        await message.reply_text("RSS feed monitoring is not running.")

