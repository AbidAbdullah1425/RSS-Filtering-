import asyncio
import feedparser
from pyrogram import Client
from pymongo import MongoClient
import re
import logging
from bot import Bot
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
tasks_collection = db["tasks"]
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
        tasks = [t["task"] for t in tasks_collection.find()]
        logger.debug(f"Current tasks: {tasks}")

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

            for task in tasks:
                if task in entry.title:
                    episode = get_episode_number(entry.title)
                    anime_name = get_task_title(entry.title)
                    magnet_link = entry.link
                    message = f"/leech {magnet_link} -n {episode} {anime_name} [1080p][@AnimeQuestX].mkv"

                    logger.info(f"Sending message to group: {message}")
                    await client.send_message(chat_id=GROUP_ID, text=message)
  # Correct argument use
                    processed_ids_collection.insert_one({"post_id": post_id})
                    break

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

    if command[0] == "/addtask" and len(command) > 1:
        task = " ".join(command[1:])
        tasks_collection.update_one({"task": task}, {"$set": {"task": task}}, upsert=True)
        await message.reply_text(f"Task '{task}' added successfully.")
        logger.info(f"Task added: {task}")

    elif command[0] == "/deltask" and len(command) > 1:
        task = " ".join(command[1:])
        tasks_collection.delete_one({"task": task})
        await message.reply_text(f"Task '{task}' deleted successfully.")
        logger.info(f"Task deleted: {task}")

    elif command[0] == "/listtasks":
        tasks = [t["task"] for t in tasks_collection.find()]
        task_list = "Tasks:\n" + "\n".join(tasks) if tasks else "No tasks found."
        await message.reply_text(task_list)
        logger.info("Listed tasks.")

    elif command[0] == "/startread":
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
