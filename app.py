#!python3.7
from telegram.ext import Updater
from telegram.ext import CommandHandler
import logging
import constants


def start(bot, update):
    logger.debug("Called start with following arguments:\n{},\n{}".format(str(bot), str(update)))
    bot.send_message(chat_id=update.message.chat_id, text=constants.CUT_THE_CITY_FIRST_MSG)


def cut_the_city(bot, update, args):
    logger.debug("Called cut the city with following arguments:\n{},\n{},\n{}".format(str(bot), str(update), str(args)))
    bot.send_message(chat_id=update.message.chat_id, text=constants.CUT_THE_CITY_FIRST_MSG)


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
cut_the_city_handler = CommandHandler('cut_the_city', cut_the_city, pass_args=True)
bot_dispatcher.add_handler(cut_the_city_handler)

bot_updater.start_polling()
bot_updater.idle()
