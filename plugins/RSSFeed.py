import asyncio
import feedparser
from pymongo import MongoClient
import re
import logging
from bot import user_client  # Importing the user account client
from config import API_HASH, API_ID, LOGGER, GROUP_ID, RSS_URL, DB_URI, DB_NAME

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

# Utility functions
def get_episode_number(title):
    match = re.search(r"E(\d+)|\((\d+)\)", title)
    return f"E{match.group(1) or match.group(2)}" if match else "E00"

def get_task_title(title):
    match = re.search(r"\[SubsPlease\]\s(.+?)\s-\s", title)
    return match.group(1) if match else "Unknown Title"

async def check_rss():
    while True:
        logger.info("Checking RSS feed for new entries...")
        feed = feedparser.parse(RSS_URL)

        for entry in feed.entries:
            post_id = entry.link  # Use link as unique identifier
            if processed_ids_collection.find_one({"post_id": post_id}):
                logger.info(f"Skipping already processed entry: {post_id}")
                continue

            # Process the new post
            episode = get_episode_number(entry.title)
            anime_name = get_task_title(entry.title)
            magnet_link = entry.link
            message = f"/leech {magnet_link} -n {episode} {anime_name} [1080p][@AnimeQuestX].mkv"

            try:
                # Send the message using the user account client
                await user_client.send_message(chat_id=GROUP_ID, text=message)
                logger.info(f"Message sent: {message}")
                # Save the post ID to avoid duplicates
                processed_ids_collection.insert_one({"post_id": post_id})
            except Exception as e:
                logger.error(f"Error sending message: {e}")

        logger.info("Waiting for the next RSS check...")
        await asyncio.sleep(120)  # Wait 2 minutes before checking again
