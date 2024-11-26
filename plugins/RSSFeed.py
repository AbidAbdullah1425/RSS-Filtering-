import asyncio
import feedparser
from pymongo import MongoClient
import re
import logging
from bot import Bot  # Importing the Bot instance from bot.py
from config import BOT_TOKEN, API_ID, API_HASH, OWNER_ID, GROUP_ID, RSS_URL, DB_URI, DB_NAME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# MongoDB setup
client = MongoClient(DB_URI)
db = client[DB_NAME]
processed_ids_collection = db["processed_ids"]

# Global variable to control reading
is_reading = False

# Utility functions
def get_episode_number(title):
    match = re.search(r"E(\d+)|\((\d+)\)", title)
    episode = f"E{match.group(1) or match.group(2)}" if match else "E00"
    logger.debug(f"Extracted episode number: {episode} from title: {title}")
    return episode

def get_task_title(title):
    match = re.search(r"\[SubsPlease\]\s(.+?)\s-\s", title)
    anime_title = match.group(1) if match else "Unknown Title"
    logger.debug(f"Extracted anime title: {anime_title} from title: {title}")
    return anime_title

async def check_rss():
    global is_reading
    while is_reading:
        logger.info("Checking RSS feed for new entries...")
        feed = feedparser.parse(RSS_URL)

        for entry in feed.entries:
            logger.debug(f"Processing entry: {entry.title}")
            post_id_match = re.search(r"\[.+?\]\s(.+?)\.mkv", entry.title)
            if not post_id_match:
                logger.warning(f"Skipping entry with unexpected title format: {entry.title}")
                continue

            post_id = post_id_match.group(1)
            if processed_ids_collection.find_one({"post_id": post_id}):
                logger.info(f"Skipping already processed entry: {post_id}")
                continue

            # Process the new post
            episode = get_episode_number(entry.title)
            anime_name = get_task_title(entry.title)
            magnet_link = entry.link
            message = f"/leech {magnet_link} -n {episode} {anime_name} [1080p][@AnimeQuestX].mkv"

            logger.info(f"Sending message to group: {message}")

            # Ensure GROUP_ID is an integer
            if isinstance(GROUP_ID, str):  # If GROUP_ID is a string, convert it to integer
                GROUP_ID = int(GROUP_ID)
            
            try:
                # Send the message to the group
                await Bot.send_message(chat_id=GROUP_ID, text=message)
                logger.info(f"Message sent to group {GROUP_ID}: {message}")
            except Exception as e:
                logger.error(f"Error sending message: {e}")
            
            # Save the post ID to avoid duplicates
            processed_ids_collection.insert_one({"post_id": post_id})

        # Wait before checking again
        logger.info("Waiting for the next RSS check...")
        await asyncio.sleep(120)  # Check RSS feed every 2 minutes

@Bot.on_message()
async def manage_tasks(client, message):
    global is_reading

    # Ensure only the owner can use these commands
    if message.from_user.id != OWNER_ID:
        logger.warning(f"Unauthorized user attempted to access bot: {message.from_user.id}")
        return

    command = message.text.split()

    if command[0] == "/startread":
        if is_reading:
            await message.reply_text("RSS feed reading is already running.")
            logger.info("Attempted to start RSS reading, but it's already running.")
        else:
            is_reading = True
            await message.reply_text("Started RSS feed reading.")
            logger.info("Started RSS feed reading.")
            await check_rss()  # Start reading process asynchronously

    elif command[0] == "/stopread":
        if not is_reading:
            await message.reply_text("RSS feed reading is not running.")
            logger.info("Attempted to stop RSS reading, but it's not running.")
        else:
            is_reading = False
            await message.reply_text("Stopped RSS feed reading.")
            logger.info("Stopped RSS feed reading.")
