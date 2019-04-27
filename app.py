#!python3.7
from telegram.ext import Updater
import logging
import constants


def cut_the_city(update, context, *args):
    logger.debug("Called cut the city with following arguments:\n{},\n{},\n{}".format(str(update), str(context), str(args)))

    bot = context.bot
    chat_id = update.message.chat_id

    bot.send_message(chat_id=chat_id, text=constants.CUT_THE_CITY_FIRST_MSG)
    pass

# Setting logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logger = logging.getLogger("logger")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)
logger.debug("Started debugging")

# Reading token
with open('config.ini') as config:
    TOKEN = config.readline().rstrip()
    logger.debug("found TOKEN == {}".format(TOKEN))

bot_updater = Updater(token=TOKEN)
bot_dispatcher = bot_updater.dispatcher
