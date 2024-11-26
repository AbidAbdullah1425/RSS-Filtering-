import asyncio
import feedparser
from pymongo import MongoClient
import re
from bot import user_client, Bot  # Import both clients
from pyrogram import filters
from config import GROUP_ID, RSS_URL, DB_URI, DB_NAME, ADMINS

# MongoDB setup
mongo_client = MongoClient(DB_URI)
db = mongo_client[DB_NAME]
processed_ids_collection = db["processed_ids"]
tasks_collection = db["tasks"]  # Collection to store tasks

# Global variables to control fetching state and task
is_fetching = False
fetch_task = None  # Stores the fetch task so it can be canceled


# Utility functions
def get_episode_number(title):
    match = re.search(r"E(\d+)|\((\d+)\)", title)
    return f"E{match.group(1) or match.group(2)}" if match else "E00"


def get_task_title(title):
    match = re.search(r"\[SubsPlease\]\s(.+?)\s-\s", title)
    return match.group(1) if match else "Unknown Title"


async def fetch_and_send_news():
    """Continuously fetches RSS feed and sends new entries."""
    global is_fetching
    while is_fetching:
        feed = feedparser.parse(RSS_URL)
        new_entries_found = False

        for entry in feed.entries:
            if not is_fetching:  # Stop fetching if toggled off
                break

            post_id = entry.link
            if processed_ids_collection.find_one({"post_id": post_id}):
                continue  # Skip if already processed

            # Extract details from the feed entry
            episode = get_episode_number(entry.title)
            anime_name = get_task_title(entry.title)
            magnet_link = entry.link
            message = f"/leech {magnet_link} -n {episode} {anime_name} [1080p][@AnimeQuestX].mkv"

            try:
                # Send message using the user account client
                await user_client.send_message(chat_id=GROUP_ID, text=message)
                # Save the post ID to the database
                processed_ids_collection.insert_one({"post_id": post_id})
                new_entries_found = True
            except Exception as e:
                print(f"Failed to send message: {e}")

            # Delay between messages to avoid spamming
            await asyncio.sleep(5)

        # Wait if no new entries were found
        if not new_entries_found:
            await asyncio.sleep(120)  # Wait 2 minutes before the next fetch


# Command to start fetching
@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("startread"))
async def start_fetching(client, message):
    global is_fetching, fetch_task

    if not is_fetching:
        is_fetching = True
        await message.reply_text("Started fetching RSS feed!")
        fetch_task = asyncio.create_task(fetch_and_send_news())  # Start the task
    else:
        await message.reply_text("Fetching is already running!")


# Command to stop fetching
@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("stopread"))
async def stop_fetching(client, message):
    global is_fetching, fetch_task

    if is_fetching:
        is_fetching = False
        if fetch_task:
            fetch_task.cancel()  # Cancel the ongoing task
            fetch_task = None
        await message.reply_text("Stopped fetching RSS feed!")
    else:
        await message.reply_text("Fetching is not running!")


# Command to list tasks
@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("listtasks"))
async def list_tasks(client, message):
    tasks = tasks_collection.find()
    task_list = "\n".join([task["name"] for task in tasks])
    if task_list:
        await message.reply_text(f"Task list:\n{task_list}")
    else:
        await message.reply_text("No tasks found.")


# Command to add a task
@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("addtasks"))
async def add_task(client, message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /addtasks <task_name>")
        return

    task_name = " ".join(message.command[1:])
    if tasks_collection.find_one({"name": task_name}):
        await message.reply_text(f"Task '{task_name}' already exists.")
    else:
        tasks_collection.insert_one({"name": task_name})
        await message.reply_text(f"Task '{task_name}' added successfully.")


# Command to delete a task
@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("deltasks"))
async def delete_task(client, message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /deltasks <task_name>")
        return

    task_name = " ".join(message.command[1:])
    result = tasks_collection.delete_one({"name": task_name})
    if result.deleted_count > 0:
        await message.reply_text(f"Task '{task_name}' deleted successfully.")
    else:
        await message.reply_text(f"Task '{task_name}' not found.")
