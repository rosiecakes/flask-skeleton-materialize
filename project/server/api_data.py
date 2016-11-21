# -*- coding: utf-8 -*-

import logging
from pprint import pprint as pp

import requests

# from name_match import *
# from utility import *
# import api_keys
from . import config

try:
    from utility import *
except:
    from project.server.utility import format_name, format_address


def get_google_restaurants(location, coordinates, rest_dict):
    """ This gets the top 20 restaurants based on location entered ranked
    by google prominence (factors in popularity, rating, etc) from
    Google Places API
    """

    r = requests.get('https://maps.googleapis.com/'
        + 'maps/api/place/nearbysearch/json'
        + '?location=' + str(coordinates[0]) + ',' + str(coordinates[1])
        + '&radius=' + str(10000)
        # + '&keyword=' + format_name(location)
        + '&type=' + 'restaurant'
        + '&key=' + config.GOOGLE_API_KEY)

    # Text search way to search for results
    # This uses more API request tokens and seems worse
    # r = requests.get('https://maps.googleapis.com/'
    #     + 'maps/api/place/textsearch/json'
    #     + '?query=restaurants+in+' + location
    #     + '&key=' + config.GOOGLE_API_KEY)

    if r.ok:
        # Currently force an error if run out of the 1000 Google API calls
        # Need to change this to show some kind of error message in HTML
        assert r.json()['status'] != "OVER_QUERY_LIMIT"
        assert len(r.json()['results']) > 0

        for item in r.json()['results']:
            restaurant = item['name']
            if 'rating' in item.keys():
                rest_dict[restaurant] = {}
                rest_dict[restaurant]['google_prominence'] = (
                    r.json()['results'].index(item) + 1)
                # rest_dict[restaurant]['address'] = item['formatted_address']
                rest_dict[restaurant]['address'] = item['vicinity']
                rest_dict[restaurant]['google_rating'] = item['rating']
                rest_dict[restaurant]['google_id'] = item['place_id']
                rest_dict[restaurant]['latitude'] = (
                    item['geometry']['location']['lat'])
                rest_dict[restaurant]['longitude'] = (
                    item['geometry']['location']['lng'])
                if float(rest_dict[restaurant]['google_rating']) < 2:
                    # Removes restaurants ratings less than 2 because
                    # we don't want bad results
                    logging.debug(restaurant
                        + " rating less than 2 in google, removing from list")
                    rest_dict.pop(restaurant, None)
            else:
                logging.debug(restaurant
                    + " not rated in google, skipping from list")


def get_zomato_city_id(coordinates):
    # This request gets the Zomato city ID based on the coordinates
    r = requests.get('https://developers.zomato.com/api/v2.1/cities'
        + '?lat=' + str(coordinates[0])
        + '&lon=' + str(coordinates[1]),
        headers=config.zomato_header)

    # Need to change this to try/except
    if r.ok:
        city_id = r.json()['location_suggestions'][0]['id']
    else:
        logging.error("ZOMATO CITY ID NOT FOUND!")
    return city_id


def get_zomato_restaurants(city_id, rest_dict):
    """ Gets the top 20 restaurants from Zomato API for the city_id"""
    # Can try and search zones but API documentation sucks, or search by
    # lat/lon for zip codes
    # Also can add functionality to search by category later
    r = requests.get('https://developers.zomato.com/api/v2.1/search' +
        '?entity_id=' + str(city_id) +
        '&entity_type=city' +
        '&count=20' +
        '&sort=rating' +
        '&order=desc',
         headers=config.zomato_header)

    if r.ok:
        for item in r.json()['restaurants']:

            """This commented portion was to avoid check for duplicates using
            name matching functions. It took too long because it had to compare
            against all restaurants stored so I just use a basic check for now
            and check for duplicates after. It saves time but the duplicates
            that aren't filted will require extra API calls
            """

            # for restaurant in rest_dict.keys():
            #     if restaurant_name_split_match(item['restaurant']['name'],
            #             restaurant):
            #         logging.debug("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            #         logging.debug("Potential duplicate restaurant found!")
            #         logging.debug("Restaurant 1: "
            #             + item['restaurant']['name'].encode('utf-8'))
            #         logging.debug("Restaurant 2: "
            #             + restaurant.encode('utf-8'))
            #         logging.debug("Address 1: "
            #             + rest_dict[restaurant]['address'].encode('utf-8'))
            #         logging.debug("Address 2: "
            #             + item['restaurant']['location']['address'].encode('utf-8'))
            #         if address_match(rest_dict[restaurant]['address'],
            #                 item['restaurant']['location']['address']):
            #             break
            # else:
            restaurant = item['restaurant']['name']
            if item['restaurant']['name'] not in rest_dict.keys():
                rest_dict[restaurant] = {}
                rest_dict[restaurant]['latitude'] = (
                    item['restaurant']['location']['latitude'])
                rest_dict[restaurant]['longitude'] = (
                    item['restaurant']['location']['longitude'])
                rest_dict[restaurant]['address'] = (
                    item['restaurant']['location']['address'])
            rest_dict[restaurant]['zomato_rating'] = (
                item['restaurant']['user_rating']['aggregate_rating'])
            rest_dict[restaurant]['zomato_id'] = item['restaurant']['id']
            rest_dict[restaurant]['zomato_review_count'] = (
                item['restaurant']['user_rating']['votes'])
            rest_dict[restaurant]['zomato_ranking'] = (
                r.json()['restaurants'].index(item) + 1)
            rest_dict[restaurant]['zomato_price'] = (
                int(item['restaurant']['price_range'])  * '$')
            rest_dict[restaurant]['avg_cost_for_2'] = (
                item['restaurant']['average_cost_for_two'])
            rest_dict[restaurant]['cuisines'] = item['restaurant']['cuisines']
            # Removes restaurants that have 0 or low ratings
            if float(rest_dict[restaurant]['zomato_rating']) < 2:
                logging.debug(restaurant
                    + " rating less than 2 in zomato, removing from list")
                rest_dict.pop(restaurant, None)


def get_google_data_for_zomato_restaurants(rest_dict):
    """ Finds restaurants from the Zomato results that did not
    intersect with Google results and fills in Google data
    for them one at a time
    """
    for restaurant in rest_dict.keys():
        if 'google_rating' not in rest_dict[restaurant].keys():
            # Search for matching restaurant using coordinates, name,
            # address, and radius
            r = requests.get('https://maps.googleapis.com/'
                + 'maps/api/place/nearbysearch/json'
                + '?location=' + rest_dict[restaurant]['latitude']
                + ',' + rest_dict[restaurant]['longitude']
                + '&radius=' + str(500)
                + '&keyword=' + format_address(rest_dict[restaurant]['address'])
                + '&name=' + format_name(restaurant)
                + '&key=' + config.GOOGLE_API_KEY)

            if r.ok:
                if len(r.json()['results']) > 0:
                    # Sometimes there are more than 1 results and need to find
                    # the correct one if it exists. Sort through results and
                    # see if any match the Google restaurant info
                    try:
                        logging.debug(str(len(r.json()['results']))
                            + " result(s) found for " + restaurant.encode('utf-8')
                            + " in google")
                    except TypeError:
                        logging.debug(str(len(r.json()['results']))
                            + " result(s) found for " + restaurant
                            + " in google")
                    # Shelving the name match for now
                    # for item in r.json()['results']:
                    #     # Check if name matches or address matches to verify
                    #     # match. There are rare situations where name match
                    #     # can't detect the match so we check address too
                    #     if (restaurant_name_split_match(restaurant, item['name'])
                    #             or address_match(rest_dict[restaurant]['address'],
                    #             item['vicinity'])):
                    #         matched_restaurant = item
                    #         break
                    else:
                        # If Zomato restaurant did not match any of results
                        # in Google, remove it
                        logging.debug("Name in google not matching close"
                            + " enough to what was in Zomato... removing")
                        rest_dict.pop(restaurant, None)
                        continue

                    # Get data now that restaurant match verified
                    # (if it's rated)
                    #
                    # Shelving the name match for now
                    #
                    # if 'rating' in matched_restaurant.keys():
                    #     rest_dict[restaurant]['google_id'] = (
                    #         matched_restaurant['place_id'])
                    #     rest_dict[restaurant]['google_rating'] = (
                    #         matched_restaurant['rating'])
                    #     # Remove restaurant if rating is low for quality
                    #     # purposes
                    #     if float(rest_dict[restaurant]['google_rating']) < 2:
                    #         logging.debug(restaurant + " rating less than 2"
                    #         + " in google, removing from list")
                    #         rest_dict.pop(restaurant, None)
                    # else:
                    #     # No results found so remove that restaurant
                    #     # from the list
                    #     logging.debug(restaurant.encode('utf-8')
                    #         + " not rated in google, removing from list")
                    #     rest_dict.pop(restaurant, None)
                else:
                    # Zero Results found
                    logging.info(r.json()['status'])
                    if r.json()['status'] == "ZERO_RESULTS":
                        try:
                            logging.info(restaurant.encode('utf-8')
                                + " found no results in google, continuing")
                        except:
                            logging.info(restaurant
                                + " found no results in google, continuing")
                        rest_dict.pop(restaurant, None)
                    if 'error_message' in r.json().keys():
                        logging.error(r.json()['error_message'])
            else:
                # Request failure
                logging.error(restaurant.encode('utf-8')
                    + "google request was not okay, status "
                    + str(r.status_code) + " " + r.json()['status'])
                logging.info(restaurant.encode('utf-8')
                    + " being removed due to request failure")
                rest_dict.pop(restaurant, None)


def get_zomato_data_for_google_restaurants(rest_dict):
    """ Finds restaurants from the Google results that did not
    intersect with Zomato results and fills in Google data
    for them one at a time
    """
    for restaurant in rest_dict.keys():
        # Search for matching restaurant using coordinates, name, and radius
        if 'zomato_rating' not in rest_dict[restaurant].keys():
            r = requests.get('https://developers.zomato.com/api/v2.1/search'
                + '?q=' + restaurant
                + '&lat=' + str(rest_dict[restaurant]['latitude'])
                + '&lon=' + str(rest_dict[restaurant]['longitude'])
                + '&radius=500'
                + '&sort=rating',
                headers=config.zomato_header)

            if r.ok:
                if len(r.json()['restaurants']) > 0:
                    # Sometimes there are more than 1 results and we need to
                    # find the correct one if it exists. Sort through results
                    # and see if any match the Google restaurant info
                    try:
                        logging.debug(str(len(r.json()['restaurants']))
                            + " results(s) found for " + restaurant.encode('utf-8')
                            + " in Zomato")
                    except TypeError:
                        logging.debug(str(len(r.json()['restaurants']))
                            + " results(s) found for " + restaurant
                            + " in Zomato")
                    # Shelving the name match for now
                    #
                    # for item in r.json()['restaurants']:
                    #     # Check if name matches or address matches to verify
                    #     # match. There are rare situations where name match
                    #     # can't detect the match so we check address too
                    #     if (restaurant_name_split_match(restaurant,
                    #                 item['restaurant']['name'])
                    #             or address_match(rest_dict[restaurant]['address'],
                    #                 item['restaurant']['location']['address'])):
                    #         matched_restaurant = item
                    #         break
                    else:
                        # If Google restaurant did not match any of results
                        # in Zomato, remove it
                        logging.debug("Name in Zomato not matching close "
                            + "enough to what was in Google... removing")
                        rest_dict.pop(restaurant, None)
                        continue
                    # Get data now that restaurant match verified
                    #
                    # rest_dict[restaurant]['zomato_id'] = (
                    #     matched_restaurant['restaurant']['id'])
                    # rest_dict[restaurant]['zomato_rating'] = (
                    #     matched_restaurant['restaurant']['user_rating']['aggregate_rating'])
                    # rest_dict[restaurant]['zomato_review_count'] = (
                    #     matched_restaurant['restaurant']['user_rating']['votes'])
                    # rest_dict[restaurant]['zomato_price'] = (
                    #     int(matched_restaurant['restaurant']['price_range']) * '$')
                    # rest_dict[restaurant]['avg_cost_for_2'] = (
                    #     matched_restaurant['restaurant']['average_cost_for_two'])
                    # rest_dict[restaurant]['cuisines'] = (
                    #     matched_restaurant['restaurant']['cuisines'])
                    #
                    # Remove restaurant if rating is low for quality purposes
                    #
                    # if float(rest_dict[restaurant]['zomato_rating']) < 2:
                    #     logging.debug(restaurant.encode('utf-8')
                    #         + " rating less than 2 in zomato, removing "
                    #         + "from list")
                    #     rest_dict.pop(restaurant, None)
                else:
                    # No results found so remove that restaurant from the list
                    logging.info(restaurant.encode('utf-8')
                        + " not found in zomato, removing from list")
                    rest_dict.pop(restaurant, None)
            else:
                # Request failure
                logging.error(restaurant.encode('utf-8')
                    + "zomato request was not okay, status "
                    + str(r.status_code))
                logging.info(restaurant.encode('utf-8')
                    + " being removed due to request failure")
                rest_dict.pop(restaurant, None)



def get_restaurant_data_from_apis(location, coordinates, rest_dict):
    """Runs all the API data collection functions to get complete
    restaurant information
    """
    get_google_restaurants(location, coordinates, rest_dict)
    city_id = get_zomato_city_id(coordinates)
    get_zomato_restaurants(city_id, rest_dict)
    # get_google_data_for_zomato_restaurants(rest_dict)
    # get_zomato_data_for_google_restaurants(rest_dict)
    # getGoogleReviewCountData()


# def getGoogleReviewCountData():
#     for restaurant in rest_dict.keys():
#         if 'google_review_count' not in rest_dict[restaurant].keys():
#             r = requests.get('https://maps.googleapis.com/'
#                 + 'maps/api/place/details/json'
#                 + '?placeid=' + rest_dict[restaurant]['google_id']
#                 + '&key=' + GOOGLE_API_KEY)
#             if r.ok:
#                 logging.debug(pp(r.json()))
#                 break
#                 if 'user_ratings_total' in r.json()['result'].keys():
#                     rest_dict[restaurant]['google_review_count'] = (
#                         r.json()['result']['user_ratings_total'])
#                 else:
#                     logging.debug(restaurant
#                         + " not rated in google, removing from list")
#                     rest_dict.pop(restaurant, None)
