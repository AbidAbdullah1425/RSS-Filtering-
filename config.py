#(©)CodeXBotz




import os
import logging
from logging.handlers import RotatingFileHandler

#Bot token @Botfather
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7582846707:AAGaiAZz3TVaKb3-hb4L2RPKLqi2KSokz0c")

#Your API ID from my.telegram.org
API_ID = int(os.environ.get("API_ID", "26254064"))

#Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "72541d6610ae7730e6135af9423b319c")

#Your db channel Id
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002322411485"))

#OWNER ID
OWNER_ID = int(os.environ.get("OWNER_ID", "5296584067"))

#Port
PORT = os.environ.get("PORT", "8080")

#Database 
DB_URI = os.environ.get("DATABASE_URI","mongodb+srv://abidabdullahown12:abidabdullah1425@cluster0.ey5z5.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DATABASE_NAME", "Cluster0")

GROUP_ID = int(os.environ.get("GROUP_ID","-1002322411485"))

RSS_URL = os.environ.get("RSS_URL","https://subsplease.org/rss/?r=sd")


CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "60"))


#force sub channel id, if you want enable force sub
FORCE_SUB_CHANNEL_1 = int(os.environ.get("FORCE_SUB_CHANNEL_1", "-1002077054432"))
FORCE_SUB_CHANNEL_2 = int(os.environ.get("FORCE_SUB_CHANNEL_2", "-1002003740934"))
FORCE_SUB_CHANNEL_3 = int(os.environ.get("FORCE_SUB_CHANNEL_3", "-1002125561929"))
FORCE_SUB_CHANNEL_4 = int(os.environ.get("FORCE_SUB_CHANNEL_4", "-1002092136573"))

TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

#start message
START_MSG = os.environ.get("START_MESSAGE", "Hello {first} I'm a bot who can store files and share it via spacial links")
try:
    ADMINS=[]
    for x in (os.environ.get("ADMINS", "5296584067").split()):
        ADMINS.append(int(x))
except ValueError:
        raise Exception("Your Admins list does not contain valid integers.")

#Force sub message 
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "You have to join our Channels First")

#set your Custom Caption here, Keep None for Disable Custom Caption
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)

#set True if you want to prevent users from forwarding files from bot
PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "False") == "True" else False

#Set true if you want Disable your Channel Posts Share button
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", None) == 'True'

BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "❌Don't send me messages directly I'm only File Share bot!"

ADMINS.append(OWNER_ID)
ADMINS.append(5296584067)

LOG_FILE_NAME = "filesharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
