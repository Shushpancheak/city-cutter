#!/bin/usr/env/python
"""
City Cutter - cuts a map of given city (address) with voronoi diagram
according to positions of given places' name. All through a telegram bot.
------------------------
Author: Maximelian Mumladze.
"""


from telegram.ext import Updater
from telegram.ext import CommandHandler
import constants
import logging
import googlemaps
from geopy.distance import geodesic
from io import BytesIO
from PIL import ImageDraw
from PIL import Image
from PIL import ImageFont
import requests
import math
import traceback
from VoronoiDiagram import voronoi


class MapPointInfo:
    def __init__(self, name, location):
        """
        location is tuple (lng, lat)
        """
        self.name = name
        self.location = location

    def get_name(self):
        """
        Return name of a point
        """
        return self.name

    def get_location(self):
        """
        Returns (lng, lat) of the point
        """
        return self.location


class CityInfo(MapPointInfo):
    """
    Provides info about selected city (or address)

    Including: radius.
    """

    def __init__(self, city_name, city_location, city_radius):
        """
        city_location is tuple (lng, lat).
        """
        super().__init__(city_name, city_location)
        self.radius = city_radius

    def get_radius(self):
        return self.radius


class MapImageInfo:
    """
    Used for managing picture of the map that will be eventually shown.
    """

    def lng_lat_coords_to_px(self, coords):
        """
        Converts (lng, lat) to (pixel_x, pixel_y)
        """
        sin_y = math.sin(coords[0] * math.pi / 180)
        world_coords = (
            256 * (0.5 + coords[1] / 360),
            256 * (0.5 - math.log((1 + sin_y) / (1 - sin_y)) / (4 * math.pi))
        )

        return (world_coords[0] * self.COORD_MODIFIER,
                world_coords[1] * self.COORD_MODIFIER)

    def get_map_image_respone(self):
        # Forming a request to gmaps API to get an image.
        # Due to lack of requests' way to not force %-encode characters,
        # we should create an url by ourselves.
        request_params = {
            'center': (str(self.city_info.get_location()[0]) +
                       ',' + str(self.city_info.get_location()[1])),
            'size': constants.CUT_THE_CITY_IMAGE_SIZE,
            'zoom': str(self.zoom),
            'scale': constants.CUT_THE_CITY_IMAGE_SCALE,
            'key': GMAPS_KEY,
            'markers': 'size:' + constants.CUT_THE_CITY_IMAGE_POINTERS_SIZE
        }

        if len(self.places_info) > 0:
            request_params['markers'] += '%7C'
            request_params['markers'] += '%7C'.join(
                [
                    ','.join(
                        (str(place_info.get_location()[0]),
                         str(place_info.get_location()[1]))
                    )
                    for place_info in self.places_info
                ]
            )

        request_params_str = '&'.join('{}={}'.format(key, val)
                                      for key, val in request_params.items())
        response = requests.get(constants.GMAPS_STATIC_MAPS_URL,
                                params=request_params_str)
        response.raise_for_status()

        return response

    def __init__(self, city_info, places_info):
        """
        Basically forms the final image.
        """
        self.city_info = city_info
        self.places_info = places_info

        # Getting the zoom which is in [0, 21]
        max_dist = 0
        for place_info1 in self.places_info:
            for place_info2 in self.places_info:
                max_dist = max(
                    max_dist,
                    geodesic(
                        place_info1.get_location(),
                        place_info2.get_location()
                    ).m
                )

        self.zoom = math.ceil(
            math.log(constants.EARTH_CIRCUMFERENCE / max_dist, 2)
        )
        logger.debug("Calculated zoom: {}".format(str(self.zoom)))

        # Used in formula px_coord = world_coord * coord_modifier
        self.COORD_MODIFIER = pow(2, self.zoom +
                                  constants.CUT_THE_CITY_IMAGE_SCALE_INT - 1)

        center_px_coords = self.lng_lat_coords_to_px(city_info.get_location())
        corner_px_coords = (
            center_px_coords[0] - constants.CUT_THE_CITY_IMAGE_SIZE_INT / 2,
            center_px_coords[1] - constants.CUT_THE_CITY_IMAGE_SIZE_INT / 2
        )
        places_px_coords = [
            self.lng_lat_coords_to_px(place_info.get_location())
            for place_info in places_info
        ]

        logger.debug("Calculated absolute px coordinates: {}".format(
            str(places_px_coords)))

        # Now relative to corner

        # Setting px coords for self.places_info
        for i in range(len(places_info)):
            self.places_info[i].px_coords = (
                places_px_coords[i][0] - corner_px_coords[0],
                places_px_coords[i][1] - corner_px_coords[1]
            )

        # Building the actual image
        response = self.get_map_image_respone()
        self.map_image = Image.open(BytesIO(response.content)).convert('RGB')

        # Changing the image
        map_draw = ImageDraw.Draw(self.map_image)

        voronoi_lines = voronoi.get_voronoi_polygons(
            [place_info.px_coords for place_info in self.places_info],
            (0, 0, constants.CUT_THE_CITY_IMAGE_SIZE_INT,
             constants.CUT_THE_CITY_IMAGE_SIZE_INT)
        )
        logger.debug("Calculated voronoi lines: {}".format(str(voronoi_lines)))

        for line in voronoi_lines:
            map_draw.line([tuple(line[0]), tuple(line[1])], fill='black')

        font = ImageFont.truetype("arial.ttf", 15)

        for place_info in self.places_info:
            map_draw.text(place_info.px_coords, place_info.get_name(),
                          fill='black', font=font)

        del map_draw

    def get_image(self):
        return self.map_image


def start(bot, update):
    """
    /start command. Types in a hello words.
    """
    logger.debug("Called start with following arguments: \
\n{},\n{}".format(str(bot), str(update)))
    bot.send_message(chat_id=update.message.chat_id,
                     text=constants.CUT_THE_CITY_FIRST_MSG)


def parse_city_place_names(args):
    """
    Finds city and place name in string of format
    ''<city-name>' '<place-name>''

    Returns a tuple (city_name, place_name)
    """
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
    logger.debug("Parsed these city/place names: {}, {}".format(city_name,
                                                                place_name))

    return (city_name, place_name)


def get_city_info(city_name, gmaps):
    # City geocode.
    city_geocode = gmaps.geocode(city_name)
    logger.debug("Found city {}, with this geocode info: {}".format(
        city_name,
        str(city_geocode))
    )
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
    logger.debug("Found {}'s city radius: {}".format(city_name,
                                                     str(city_radius)))

    return CityInfo(city_name, city_loc, city_radius)


def get_places_info(city_info, place_name, gmaps):
    # Finding places.
    places_info = gmaps.places_nearby(name=place_name,
                                      location=city_info.get_location(),
                                      rank_by='distance')
    logger.debug("Found list of places: {}".format(str(places_info)))

    # Storing their coordinates.
    places_locs = [(found_place['geometry']['location']['lat'],
                    found_place['geometry']['location']['lng'])
                   for found_place in places_info['results']]
    places_names = [found_place['name']
                    for found_place in places_info['results']]
    logger.debug("Places coordinates: {}".format(str(places_locs)))

    return [MapPointInfo(name, loc) for loc, name in
            zip(places_locs, places_names)]


def cut_the_city(bot, update, args):
    """
    Main command.
    """
    logger.debug("Called cut the city with following arguments: \
\n{},\n{},\n{}".format(str(bot), str(update), str(args)))

    bot.send_message(chat_id=update.message.chat_id,
                     text=constants.CUT_THE_CITY_FIRST_MSG)

    try:
        gmaps = googlemaps.Client(key=GMAPS_KEY)
        city_name, place_name = parse_city_place_names(args)
        city_info = get_city_info(city_name, gmaps)
        places_info = get_places_info(city_info, place_name, gmaps)

        map_image_info = MapImageInfo(city_info, places_info)

        # Sending the final result
        map_image = map_image_info.get_image()
        final_image_file = BytesIO()
        final_image_file.name = 'pic.png'
        map_image.save(final_image_file, 'PNG')
        final_image_file.seek(0)

        bot.send_message(chat_id=update.message.chat_id,
                         text=constants.CUT_THE_CITY_SUCCESS_MSG)
        bot.send_photo(chat_id=update.message.chat_id,
                       photo=final_image_file)
    except:
        traceback.print_exc()
        bot.send_message(chat_id=update.message.chat_id,
                         text=constants.CUT_THE_CITY_ERROR_MSG)


# Setting logger
logging.basicConfig(format='%(asctime)s - %(name)s -\
 %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger("logger")
logger.setLevel(constants.LOGGING_LEVEL)
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
cut_the_city_handler = CommandHandler('cut_the_city', cut_the_city,
                                      pass_args=True)
bot_dispatcher.add_handler(cut_the_city_handler)

bot_updater.start_polling()
bot_updater.idle()
