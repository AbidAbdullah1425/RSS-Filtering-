import asyncio
import feedparser
import logging
from pyrogram import Client, filters
from pymongo import MongoClient
from config import RSS_URL, GROUP_ID, OWNER_ID, DB_URI, DB_NAME
from bot import Bot, User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RSSBot")

# MongoDB setup
mongo_client = MongoClient(DB_URI)
db = mongo_client[DB_NAME]
anime_collection = db["anime_names"]
rss_collection = db["rss_entries"]

is_reading = False  # Flag to track reading status


async def fetch_and_send_anime():
    """Fetch matching anime titles from the RSS feed and send them to the group."""
    global is_reading
    logger.info("Starting RSS feed reading...")
    while is_reading:
        try:
            feed = feedparser.parse(RSS_URL)
            anime_names = [anime["name"] for anime in anime_collection.find()]

            for entry in feed.entries:
                title = entry.title
                link = entry.link

                if rss_collection.find_one({"link": link}):
                    continue

                if any(name.lower() in title.lower() for name in anime_names):
                    if not User.is_connected:
                        logger.error("User client is not connected. Cannot send message.")
                        continue

                    await User.send_message(
                        GROUP_ID,
                        f"**{title}**\n[Read More]({link})",
                        disable_web_page_preview=True,
                    )
                    rss_collection.insert_one({"link": link, "title": title})

            logger.info("RSS feed processed. Sleeping for 2 minutes.")
            await asyncio.sleep(120)  # 2-minute interval

        except Exception as e:
            logger.error(f"Error in fetch_and_send_anime: {e}")


@Bot.on_message(filters.command("startread") & filters.private & filters.user(OWNER_ID))
async def start_read(_, message):
    global is_reading
    if is_reading:
        await message.reply_text("Already reading the RSS feed.")
    else:
        is_reading = True
        await message.reply_text("Started reading the RSS feed.")
        asyncio.create_task(fetch_and_send_anime())


@Bot.on_message(filters.command("stopread") & filters.private & filters.user(OWNER_ID))
async def stop_read(_, message):
    global is_reading
    if not is_reading:
        await message.reply_text("Not currently reading the RSS feed.")
    else:
        is_reading = False
        await message.reply_text("Stopped reading the RSS feed.")


@Bot.on_message(filters.command("startuser") & filters.private & filters.user(OWNER_ID))
async def start_user_client(_, message):
    """Force-start the User client."""
    if User.is_connected:
        await message.reply_text("User client is already running.")
    else:
        try:
            logger.info("Starting User client...")
            await User.start()
            await message.reply_text("User client started successfully!")
        except Exception as e:
            logger.error(f"Failed to start User client: {e}")
            await message.reply_text("Failed to start User client. Please check the logs.")


@Bot.on_message(filters.command("listtasks") & filters.private & filters.user(OWNER_ID))
async def list_tasks(_, message):
    anime_names = [anime["name"] for anime in anime_collection.find()]
    if anime_names:
        await message.reply_text("Tracked anime:\n" + "\n".join(anime_names))
    else:
        await message.reply_text("No anime is currently being tracked.")


@Bot.on_message(filters.command("addtasks") & filters.private & filters.user(OWNER_ID))
async def add_task(_, message):
    args = message.text.split(" ", 1)
    if len(args) < 2:
        await message.reply_text("Usage: /addtasks <anime_name>")
        return

    anime_name = args[1].strip()
    if anime_collection.find_one({"name": anime_name}):
        await message.reply_text(f"`{anime_name}` is already being tracked.")
    else:
        anime_collection.insert_one({"name": anime_name})
        await message.reply_text(f"Added `{anime_name}` to the tracked list.")


@Bot.on_message(filters.command("deltasks") & filters.private & filters.user(OWNER_ID))
async def delete_task(_, message):
    args = message.text.split(" ", 1)
    if len(args) < 2:
        await message.reply_text("Usage: /deltasks <anime_name>")
        return

    anime_name = args[1].strip()
    result = anime_collection.delete_one({"name": anime_name})
    if result.deleted_count:
        await message.reply_text(f"Removed `{anime_name}` from the tracked list.")
    else:
        await message.reply_text(f"`{anime_name}` is not in the tracked list.")


async def start_bot():
    """Start the bot and User client."""
    try:
        logger.info("Starting Pyrogram bot...")
        await Bot.start()
        logger.info("Bot started successfully.")

        if not User.is_connected:
            logger.info("Starting User client...")
            await User.start()
            logger.info("User client started successfully.")

        await Bot.idle()
    finally:
        await Bot.stop()
        if User.is_connected:
            await User.stop()
        logger.info("Bot and User client stopped.")


# Run the bot (without asyncio.run())
asyncio.create_task(start_bot())
