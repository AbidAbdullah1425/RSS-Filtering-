import feedparser
from pyrogram import Client
from pymongo import MongoClient
import re
from config import BOT_TOKEN, API_ID, API_HASH, OWNER_ID, GROUP_ID, RSS_URL, DB_URI, DB_NAME

# MongoDB setup
client = MongoClient(DB_URI)
db = client[DB_NAME]
tasks_collection = db["tasks"]
processed_ids_collection = db["processed_ids"]

# Pyrogram bot setup
bot = Client("rss_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Utility functions
def get_episode_number(title):
    match = re.search(r"E(\d+)|\((\d+)\)", title)
    return f"E{match.group(1) or match.group(2)}" if match else "E00"

def get_task_title(title):
    match = re.search(r"\[SubsPlease\]\s(.+?)\s-\s", title)
    return match.group(1) if match else "Unknown Title"

@bot.on_message()
async def manage_tasks(client, message):
    if message.from_user.id != OWNER_ID:
        return

    command = message.text.split()
    if command[0] == "/addtask" and len(command) > 1:
        task = " ".join(command[1:])
        tasks_collection.update_one({"task": task}, {"$set": {"task": task}}, upsert=True)
        await message.reply_text(f"Task '{task}' added successfully.")
    elif command[0] == "/deltask" and len(command) > 1:
        task = " ".join(command[1:])
        tasks_collection.delete_one({"task": task})
        await message.reply_text(f"Task '{task}' deleted successfully.")
    elif command[0] == "/listtasks":
        tasks = [t["task"] for t in tasks_collection.find()]
        await message.reply_text("Tasks:\n" + "\n".join(tasks) if tasks else "No tasks found.")

async def check_rss():
    feed = feedparser.parse(RSS_URL)
    tasks = [t["task"] for t in tasks_collection.find()]

    for entry in feed.entries:
        post_id = re.search(r"\[(.+?)\]\.mkv", entry.title).group(1)
        if processed_ids_collection.find_one({"post_id": post_id}):
            continue

        for task in tasks:
            if task in entry.title:
                episode = get_episode_number(entry.title)
                anime_name = get_task_title(entry.title)
                magnet_link = entry.link
                message = f"/leech {magnet_link} -n {episode} {anime_name} [1080p][@AnimeQuestX]"
                
                await bot.send_message(GROUP_ID, message)
                processed_ids_collection.insert_one({"post_id": post_id})
                break

# Start the bot and schedule RSS checks
async def main():
    async with bot:
        while True:
            await check_rss()
            await asyncio.sleep(120)  # Check RSS feed every 2 minutes
