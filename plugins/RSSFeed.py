import asyncio
import feedparser
from pyrogram import Client, filters
from pymongo import MongoClient
from config import BOT_TOKEN, API_ID, API_HASH, RSS_URL, GROUP_ID, OWNER_ID, STRING_SESSION, DB_URI, DB_NAME

# MongoDB setup
mongo_client = MongoClient(DB_URI)
db = mongo_client[DB_NAME]
anime_collection = db["anime_names"]
rss_collection = db["rss_entries"]

# Pyrogram Clients
bot_client = Client("Bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)
user_client = Client("User", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

is_reading = False  # Flag to track reading status


async def fetch_and_send_anime():
    """Fetch matching anime titles from the RSS feed and send them to the group."""
    global is_reading
    while is_reading:
        feed = feedparser.parse(RSS_URL)
        anime_names = [anime["name"] for anime in anime_collection.find()]

        for entry in feed.entries:
            title = entry.title
            link = entry.link

            if rss_collection.find_one({"link": link}):
                continue

            if any(name.lower() in title.lower() for name in anime_names):
                await user_client.send_message(
                    GROUP_ID,
                    f"**{title}**\n[Read More]({link})",
                    disable_web_page_preview=True
                )
                rss_collection.insert_one({"link": link, "title": title})

        await asyncio.sleep(120)  # 2-minute interval


@bot_client.on_message(filters.command("startread") & filters.private & filters.user(OWNER_ID))
async def start_read(_, message):
    global is_reading
    if is_reading:
        await message.reply_text("Already reading the RSS feed.")
    else:
        is_reading = True
        await message.reply_text("Started reading the RSS feed.")
        asyncio.create_task(fetch_and_send_anime())


@bot_client.on_message(filters.command("stopread") & filters.private & filters.user(OWNER_ID))
async def stop_read(_, message):
    global is_reading
    if not is_reading:
        await message.reply_text("Not currently reading the RSS feed.")
    else:
        is_reading = False
        await message.reply_text("Stopped reading the RSS feed.")


@bot_client.on_message(filters.command("listtasks") & filters.private & filters.user(OWNER_ID))
async def list_tasks(_, message):
    anime_names = [anime["name"] for anime in anime_collection.find()]
    if anime_names:
        await message.reply_text("Tracked anime:\n" + "\n".join(anime_names))
    else:
        await message.reply_text("No anime is currently being tracked.")


@bot_client.on_message(filters.command("addtasks") & filters.private & filters.user(OWNER_ID))
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


@bot_client.on_message(filters.command("deltasks") & filters.private & filters.user(OWNER_ID))
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


async def main():
    """Main function to manage both clients."""
    try:
        await user_client.start()
        await bot_client.start()

        print("[INFO] - Both clients started successfully.")
        await bot_client.idle()
    except KeyboardInterrupt:
        print("[INFO] - Shutting down bot...")
    finally:
        await user_client.stop()
        await bot_client.stop()
        print("[INFO] - Both clients stopped.")


