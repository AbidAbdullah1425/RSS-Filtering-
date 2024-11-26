import logging
from bot import Bot  # Import the Bot instance from bot.py
from config import GROUP_ID
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Handle /test command
@Bot.on_message(filters.text & filters.command("test"))
async def send_test_message(client, message):
    try:
        # Logging the group ID to verify it is set correctly
        logger.info(f"Sending test message to group ID: {GROUP_ID}")
        
        # Sending a test message to the group
        response = await Bot.send_message(chat_id=GROUP_ID, text="Test message from bot!")
        logger.info(f"Message sent successfully: {response}")
        await message.reply("Test message sent to group!")
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        await message.reply(f"Failed to send test message: {e}")

