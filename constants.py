import logging


CUT_THE_CITY_START_MSG = "Hello!\nUse /cut_the_city 'city_name' 'place_name'\
\nExample: /cut_the_city 'Barcelona' 'Store'"
CUT_THE_CITY_FIRST_MSG = "I'm gonna cut this city and give you the image,\
unless you've messed something up..."
CUT_THE_CITY_ERROR_MSG = "Sorry, something's gone wrong. No image for you.\
Try again!"
CUT_THE_CITY_SUCCESS_MSG = "Here you go!"

CUT_THE_CITY_IMAGE_SIZE_INT_RAW = 640
CUT_THE_CITY_IMAGE_SIZE = 'x'.join((str(CUT_THE_CITY_IMAGE_SIZE_INT_RAW),
                                    str(CUT_THE_CITY_IMAGE_SIZE_INT_RAW)))
CUT_THE_CITY_IMAGE_SCALE_INT = 2
CUT_THE_CITY_IMAGE_SCALE = str(CUT_THE_CITY_IMAGE_SCALE_INT)
CUT_THE_CITY_IMAGE_SIZE_INT = (CUT_THE_CITY_IMAGE_SCALE_INT *
                               CUT_THE_CITY_IMAGE_SIZE_INT_RAW)
CUT_THE_CITY_IMAGE_POINTERS_SIZE = 'tiny'
CUT_THE_CITY_IMAGE_POINT_RADIUS = 5

CUT_THE_CITY_DEFAULT_CITY_RADIUS = 500  # m

GMAPS_STATIC_MAPS_URL = "http://maps.google.com/maps/api/staticmap"

EARTH_CIRCUMFERENCE = 40075017

LOGGING_LEVEL = logging.ERROR
