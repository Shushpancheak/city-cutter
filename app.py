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
import math


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
        if 'bounds' in city_geocode[0]['geometry']:
            bound_loc_set = city_geocode[0]['geometry']['bounds']['northeast']
            bound_loc = (bound_loc_set['lat'], bound_loc_set['lng'])
            city_radius = int(abs(geodesic(city_loc, bound_loc).m))
        else:
            city_radius = constants.CUT_THE_CITY_DEFAULT_CITY_RADIUS
        logger.debug("Found {}'s city radius: {}".format(city_name, str(city_radius)))

        # Finding places.
        places_info = gmaps.places_nearby(name=place_name, location=city_loc, rank_by='distance')
        logger.debug("Found list of places: {}".format(str(places_info)))

        # Stroing their coordinates.
        places_locs_raw = [(found_place['geometry']['location']['lat'],
                        found_place['geometry']['location']['lng'])
                        for found_place in places_info['results']]
        logger.debug("Raw places coordinates: {}".format(str(places_locs_raw)))

        # Deleting those who exceed city radius
        logger.debug("Places distances ({}):".format(str(len(places_locs_raw))))
        places_locs = []
        for place_loc_raw in places_locs_raw:
            logger.debug(str(abs(geodesic(city_loc, place_loc_raw).m)))
            if abs(geodesic(city_loc, place_loc_raw).m) > city_radius:
                logger.debug("^EXCEEDS")
            else:
                places_locs += [place_loc_raw]

        logger.debug("Now we have ({}) places:".format(str(len(places_locs))))

        # Getting the zoom which is in [0, 21]
        max_dist = 0
        for place_loc1 in places_locs:
            for place_loc2 in places_locs:
                max_dist = max(max_dist, geodesic(place_loc1, place_loc2).m)

        zoom = math.ceil(math.log(constants.EARTH_CIRCUMFERENCE / max_dist, 2))
        logger.debug("Calculated zoom: {}".format(str(zoom)))

        # Forming a request to gmaps API to get an image.
        request_params = {
            'center': '(' + str(city_loc[0]) + ',' + str(city_loc[1]) + ')',
            'size': constants.CUT_THE_CITY_IMAGE_SIZE,
            'zoom': str(zoom),
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

        # Converting everything to pixels
        # Using this formula: pixelCoordinate = worldCoordinate * 2^zoomLevel.
        # Multiplying by 2 becasue of the scale.
        COORD_MODIFIER = pow(2, zoom + constants.CUT_THE_CITY_IMAGE_SCALE_INT - 1)
        def world_coords_to_px(coords):
            return (coords[1] * COORD_MODIFIER, coords[0] * COORD_MODIFIER)
        center_px_coords = world_coords_to_px(city_loc)
        corner_px_coords = (center_px_coords[0] - constants.CUT_THE_CITY_IMAGE_SIZE_INT / 2,
                            center_px_coords[1] + constants.CUT_THE_CITY_IMAGE_SIZE_INT / 2)
        places_px_coords = [world_coords_to_px(loc) for loc in places_locs]

        logger.debug("Calculated absolute px coordinates: {}".format(str(places_px_coords)))

        # Now relative to corner
        places_px_rel_coords = [(loc[0] - corner_px_coords[0], -loc[1] + corner_px_coords[1])
                                for loc in places_px_coords]

        logger.debug("Calculated px coordinates: {}".format(str(places_px_rel_coords)))

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
