#!/bin/usr/env/python

from telegram.ext import Updater
from telegram.ext import CommandHandler
import logging
import constants
import googlemaps
from geopy.distance import geodesic
from io import BytesIO
from PIL import Image
import requests


def start(bot, update):
    logger.debug("Called start with following arguments:\n{},\n{}".format(str(bot), str(update)))
    bot.send_message(chat_id=update.message.chat_id, text=constants.CUT_THE_CITY_FIRST_MSG)


def cut_the_city(bot, update, args):
    logger.debug("Called cut the city with following arguments:\n{},\n{},\n{}".format(str(bot), str(update), str(args)))
    bot.send_message(chat_id=update.message.chat_id, text=constants.CUT_THE_CITY_FIRST_MSG)

    try:
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

        # City geocode.
        city_geocode = gmaps.geocode(city_name)
        logger.debug("Found city {}, with this geocode info: {}".format(city_name, str(city_geocode)))
        location_set = city_geocode[0]['geometry']['location']
        city_loc = (location_set['lat'], location_set['lng'])
        logger.debug("Parsed location: {}".format(str(city_loc)))

        # Finding City radius.
        bound_loc_set = city_geocode[0]['geometry']['bounds']['northeast']
        bound_loc = (bound_loc_set['lat'], bound_loc_set['lng'])

        city_radius = abs(geodesic(city_loc, bound_loc).m)
        logger.debug("Found {}'s city radius: {}".format(city_name, str(city_radius)))

        # Finding places.
        places_info = gmaps.places(place_name, location=city_loc, radius=city_radius)
        logger.debug("Found list of places: {}".format(str(places_info)))

        # Stroing their coordinates.
        places_locs = [(found_place['geometry']['location']['lat'],
                        found_place['geometry']['location']['lng'])
                        for found_place in places_info['results']]

        # Forming a request to gmaps API to get an image.
        request_params = {
            'center': city_name,
            'size': constants.CUT_THE_CITY_IMAGE_SIZE,
            'scale': constants.CUT_THE_CITY_IMAGE_SCALE,
            'markers': 'size:' + constants.CUT_THE_CITY_IMAGE_POINTERS_SIZE,
            'key': GMAPS_KEY
        }

        if len(places_locs) > 0:
            request_params['markers'] += '%7C'
            request_params['markers'] += '%7C'.join([','.join((str(loc[0]), str(loc[1])))
                                                     for loc in places_locs])

        # Sending request

        # Due to lack of requests' way to not force %-encode characters,
        # we should create an url by ourselves.
        request_params_str = '&'.join('{}={}'.format(key, val) for key, val in request_params.items())
        response = requests.get(constants.GMAPS_STATIC_MAPS_URL, params=request_params_str)
        response.raise_for_status()

        # Building the actual image
        image = Image.open(BytesIO(response.content))

        # Sending the final result
        final_image_file = BytesIO()
        final_image_file.name = city_name
        image.save(final_image_file, 'PNG')
        final_image_file.seek(0)

        bot.send_message(chat_id=update.message.chat_id, text=constants.CUT_THE_CITY_SUCCESS_MSG)
        bot.send_photo(chat_id=update.message.chat_id, photo=final_image_file)
    except:
        import traceback
        traceback.print_exc()
        bot.send_message(chat_id=update.message.chat_id, text=constants.CUT_THE_CITY_ERROR_MSG)


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
