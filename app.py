#!/bin/usr/env/python

from telegram.ext import Updater
from telegram.ext import CommandHandler
import logging
import constants
import googlemaps


def start(bot, update):
    logger.debug("Called start with following arguments:\n{},\n{}".format(str(bot), str(update)))
    bot.send_message(chat_id=update.message.chat_id, text=constants.CUT_THE_CITY_FIRST_MSG)


def cut_the_city(bot, update, args):
    logger.debug("Called cut the city with following arguments:\n{},\n{},\n{}".format(str(bot), str(update), str(args)))
    bot.send_message(chat_id=update.message.chat_id, text=constants.CUT_THE_CITY_FIRST_MSG)

    city_name = ""
    place_name = ""
    i = 0
    for word in args:
        if word[0] == "'":
            i += 1
        if i == 1:
            city_name += word + " "
        else:
            place_name += word + " "

    city_name = city_name.replace("'", "").rstrip()
    place_name = place_name.replace("'", "").rstrip()
    logger.debug("Got these city/place names: {}, {}".format(city_name, place_name))

    gmaps = googlemaps.Client(key=GMAPS_KEY)

    city_geocode = gmaps.geocode(city_name)
    logger.debug("Found city {}, with this geocode info: {}".format(city_name, str(city_geocode)))
    location_set = city_geocode[0]['geometry']['location']
    location = (location_set['lat'], location_set['lng'])
    logger.debug("Parsed location: {}".format(str(location)))

    places_info = gmaps.places(place_name, location=location)
    logger.debug("Found list of places: {}".format(str(places_info)))



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
    TG_TOKEN = config.readline().rstrip()
    logger.debug("found TG_TOKEN == {}".format(TG_TOKEN))

    GMAPS_KEY = config.readline().rstrip()
    logger.debug("found GMAPS_KEY == {}".format(GMAPS_KEY))

bot_updater = Updater(token=TG_TOKEN)
bot_dispatcher = bot_updater.dispatcher
cut_the_city_handler = CommandHandler('cut_the_city', cut_the_city, pass_args=True)
bot_dispatcher.add_handler(cut_the_city_handler)

bot_updater.start_polling()
bot_updater.idle()
