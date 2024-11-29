import asyncio
import sys
from datetime import datetime
from aiohttp import web
from pyrogram import Client, errors
from pyrogram.enums import ParseMode
import pyrogram.utils
from config import API_HASH, API_ID, LOGGER, BOT_TOKEN, TG_BOT_WORKERS, GROUP_ID, PORT, STRING_SESSION
from plugins import web_server

# Configure the minimum channel ID for Pyrogram
pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

# Create the user client instance for interaction with the Telegram API
User = Client(
    name="User",
    api_hash=API_HASH,
    api_id=API_ID,
    session_string=STRING_SESSION,
    workers=TG_BOT_WORKERS,
    plugins={"root": "plugins"}
)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=API_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        try:
            db_group = await self.get_chat(GROUP_ID)
            self.db_group = db_group

            # Check bot's admin rights in the group
            bot_member = await self.get_chat_member(chat_id=db_group.id, user_id=self.me.id)
            if not bot_member.privileges or not bot_member.privileges.can_manage_chat:
                raise PermissionError(
                    f"Bot lacks necessary admin permissions in the group. Current permissions: {bot_member.privileges}"
                )

            # Send a test message to confirm access
            test_message = await self.send_message(chat_id=db_group.id, text="Test Message")
            await test_message.delete()
        except PermissionError as perm_error:
            self.LOGGER(__name__).warning(perm_error)
            self.LOGGER(__name__).warning(
                f"Ensure the bot is an admin in the group and can manage the chat. Current GROUP_ID value: {GROUP_ID}"
            )
            self.LOGGER(__name__).info("\nBot Stopped. Join https://t.me/weebs_support for support")
            sys.exit()
        except Exception as e:
            self.LOGGER(__name__).warning(e)
            self.LOGGER(__name__).warning(
                f"Double-check the GROUP_ID value. Current value: {GROUP_ID}"
            )
            self.LOGGER(__name__).info("\nBot Stopped. Join https://t.me/weebs_support for support")
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info("Bot Running..!")
        self.LOGGER(__name__).info(r"""       
  ___ ___  ___  ___ ___ _    _____  _____  ___ _____ ___ 
 / __/ _ \|   \| __| __| |  |_ _\ \/ / _ )/ _ \_   _/ __|
| (_| (_) | |) | _|| _|| |__ | | >  <| _ \ (_) || | \__ \\
 \___\___/|___/|___|_| |____|___/_/\_\___/\___/ |_| |___/
                                                         
""")
        self.username = usr_bot_me.username

        # Web-response
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

# Start the user client
async def start_user_client():
    try:
        await User.start()
        LOGGER(__name__).info("User client started successfully. Username: " + (await User.get_me()).username)
    except errors.FloodWait as e:
        LOGGER(__name__).error(f"Flood wait error: {e}")
        sys.exit()
    except Exception as e:
        LOGGER(__name__).error(f"Failed to start User client: {e}")
        sys.exit()

# Main function to start both clients
async def main():
    await start_user_client()
    bot = Bot()
    await bot.start()

# Start execution
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
