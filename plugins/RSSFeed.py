import asyncio
import feedparser
import logging
from pyrogram import Client
from pymongo import MongoClient
import re
from bot import Bot
from config import BOT_TOKEN, API_ID, API_HASH, OWNER_ID, GROUP_ID, RSS_URL, DB_URI, DB_NAME

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# MongoDB setup
logger.info("Connecting to MongoDB...")
client = MongoClient(DB_URI)
db = client[DB_NAME]
tasks_collection = db["tasks"]
processed_ids_collection = db["processed_ids"]

logger.info("MongoDB connection established.")

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
    task_title = match.group(1) if match else "Unknown Title"
    logger.debug(f"Extracted task title: {task_title} from title: {title}")
    return task_title

async def check_rss():
    global is_reading
    logger.info("Started RSS feed checking loop.")
    while is_reading:
        try:
            logger.info("Fetching RSS feed...")
            feed = feedparser.parse(RSS_URL)
            tasks = [t["task"] for t in tasks_collection.find()]
            logger.info(f"Active tasks: {tasks}")

            for entry in feed.entries:
                logger.debug(f"Processing RSS entry: {entry.title}")
                post_id_match = re.search(r"\[(.+?)\]\.mkv", entry.title)
                if not post_id_match:
                    logger.warning(f"Post ID not found in title: {entry.title}")
                    continue

                post_id = post_id_match.group(1)
                if processed_ids_collection.find_one({"post_id": post_id}):
                    logger.info(f"Post ID {post_id} already processed. Skipping...")
                    continue

                for task in tasks:
                    if task in entry.title:
                        episode = get_episode_number(entry.title)
                        anime_name = get_task_title(entry.title)
                        magnet_link = entry.link
                        message = f"/leech {magnet_link} -n {episode} {anime_name} [1080p][@AnimeQuestX].mkv"

                        logger.info(f"Sending message to group: {message}")
                        await bot.send_message(GROUP_ID, message)
                        processed_ids_collection.insert_one({"post_id": post_id})
                        logger.info(f"Marked post ID {post_id} as processed.")
                        break

            await asyncio.sleep(120)  # Check RSS feed every 2 minutes
        except Exception as e:
            logger.error(f"Error in RSS feed checking loop: {e}")

@Bot.on_message()
async def manage_tasks(client, message):
    global is_reading

    # Ensure only the owner can use these commands
    if message.from_user.id != OWNER_ID:
        logger.warning(f"Unauthorized user {message.from_user.id} tried to use the bot.")
        return

    command = message.text.split()
    logger.info(f"Received command: {command} from user {message.from_user.id}")

    if command[0] == "/addtask" and len(command) > 1:
        task = " ".join(command[1:])
        tasks_collection.update_one({"task": task}, {"$set": {"task": task}}, upsert=True)
        logger.info(f"Task '{task}' added.")
        await message.reply_text(f"Task '{task}' added successfully.")

    elif command[0] == "/deltask" and len(command) > 1:
        task = " ".join(command[1:])
        tasks_collection.delete_one({"task": task})
        logger.info(f"Task '{task}' deleted.")
        await message.reply_text(f"Task '{task}' deleted successfully.")

    elif command[0] == "/listtasks":
        tasks = [t["task"] for t in tasks_collection.find()]
        logger.info("Listing tasks.")
        await message.reply_text("Tasks:\n" + "\n".join(tasks) if tasks else "No tasks found.")

    elif command[0] == "/startread":
        if is_reading:
            logger.info("RSS feed reading already running.")
            await message.reply_text("RSS feed reading is already running.")
        else:
            is_reading = True
            logger.info("Started RSS feed reading.")
            await message.reply_text("Started RSS feed reading.")
            asyncio.create_task(check_rss())  # Start reading process asynchronously

    elif command[0] == "/stopread":
        if not is_reading:
            logger.info("RSS feed reading not running.")
            await message.reply_text("RSS feed reading is not running.")
        else:
            is_reading = False
            logger.info("Stopped RSS feed reading.")
            await message.reply_text("Stopped RSS feed reading.")
