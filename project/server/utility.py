# -*- coding: utf-8 -*-

import logging
import itertools
import collections
import time

# import name_match


def format_name(name):
    """Remove non alphanumeric/whitespace characers from user input or 
    restaurant data
    """
    return ''.join(chr for chr in name if chr.isalnum() or chr.isspace())


def format_address(address):
    """Remove non alphanumeric/whitespace characers from restaurant address 
    but allows for commas
    """
    return ''.join(chr for chr in address if chr.isalnum() 
        or chr.isspace() or chr == ",")


def scrub_tablename(tablename):
    """Removes whitespace characters from location so can save table name, 
    adds _ before name if all numbers
    """
    table = ''.join(chr for chr in tablename if chr.isalnum())
    if table[0].isdigit():
        table = "_" + table
    return table.upper()


def get_potential_duplicates(rest_dict):
    """We want to check for duplicates in the restaurant dictionary.
    Review count is usually unique so we want to check for matching 
    review count numbers and then compare them for any name matches
    """

    # Create a temporary dictionary of just restaurant names and review 
    # count as value because that is all we care about here
    temp_dict = {}
    for restaurant in rest_dict:
        temp_dict[restaurant] = rest_dict[restaurant]['zomato_review_count']

    # Count occurrences of each review count 
    review_count_occurrences = collections.Counter(temp_dict.values())

    # Get a list of the review count occurrences that happen more than once
    potential_duplicates = list(set([value for key, value in temp_dict.items()
                                if review_count_occurrences[value] > 1]))

    # Pull out lists of the restaurant names that have matching review counts 
    # in separate lists for each so they only check against same review count
    restaurants_to_check = [[key for key, value in temp_dict.items() 
                                if value == num] 
                                for num in potential_duplicates]    
    return restaurants_to_check


def check_duplicate_restaurant(rest_dict, rest1, rest2):
    """Checks to see if two restaurants are duplicates"""
    # I can tweak this to use address matching as well
    # Check to see if ratings are the same and name matches
    if ((rest_dict[rest1]['google_rating'] == 
                rest_dict[rest2]['google_rating']) 
            and (rest_dict[rest1]['zomato_rating'] == 
                rest_dict[rest2]['zomato_rating']) 
            and name_match.restaurant_name_split_match(rest1, rest2)):
        logging.debug("Duplicate restaurants found: " + rest1.encode('utf-8') 
            + " and " + rest2.encode('utf-8'))
        return True
    logging.debug("Potential duplicate restaurants that failed test: " 
        + rest1.encode('utf-8') + " and " + rest2.encode('utf-8'))
    return False


def find_duplicate_restaurants(rest_dict):
    """Checks all combinations of potential duplicates and adds
    duplicates to a list as a pair
    """
    logging.debug("Checking for potential duplicate restaurants...")
    duplicate_pairs = []
    restaurants_to_check = get_potential_duplicates(rest_dict)
    for potential_duplicates_list in restaurants_to_check:
        # Check all combinations of restaurants that have matching 
        # review counts
        for rest1, rest2 in itertools.combinations(
                potential_duplicates_list, 2):
            if check_duplicate_restaurant(rest_dict, rest1, rest2):
                duplicate_pairs.append([rest1, rest2])
    return duplicate_pairs


def remove_duplicate_restaurants(rest_dict):
    """Removes duplicate restaurants from restaurant dict"""
    duplicate_pairs = find_duplicate_restaurants(rest_dict)
    for duplicate_pair in duplicate_pairs:
        logging.debug("Removing duplicate restaurant: "
            + duplicate_pair[0].encode('utf-8'))
        rest_dict.pop(duplicate_pair[0], None)                       


def calculate_statistics(rest_dict):
    """Calculates average rating and Restaurate ranking for each restaurant
    This gets a weighted ranking of of rating and popularity to get the
    'restaurate rank'
    """
    # Calculates average rating from google and zomato for each restaurant
    for restaurant in rest_dict.keys():
        if ('zomato_rating' in rest_dict[restaurant].keys() and 'google_rating' 
                in rest_dict[restaurant].keys()):
            rest_dict[restaurant]['average_rating'] = (
                (float(rest_dict[restaurant]['google_rating']) 
                + float(rest_dict[restaurant]['zomato_rating'])) / 2)
            # This counted total reviews before google removed this data
            # from it's API. Left it here for if we get Tripadvisor
            # review count later
            rest_dict[restaurant]['total_reviews'] = (
                int(rest_dict[restaurant]['zomato_review_count']))
        else:
            # Error if we somehow get here and each restaurant
            # doesn't have ratings from each site
            logging.error("This place got to calculate_statistics without " 
                + "all its rating data: ", restaurant)
            logging.error(rest_dict[restaurant])
            break

    # Make a list that sorts restaurant dictionary by rating
    sorted_rating = sorted(rest_dict, 
        key=lambda x: (rest_dict[x]['average_rating']), reverse=True)
    # Make a list that sorts restaurant dictionary by total review count
    sorted_popularity = sorted(rest_dict, 
        key=lambda x: (rest_dict[x]['total_reviews']), reverse=True)
    # Stores the ranking order for rating and review count (popularity)
    # and saves them for each restaurant in the dictionary
    for restaurant in rest_dict:
        rest_dict[restaurant]['rating_rank'] = (
            sorted_rating.index(restaurant) + 1)
        rest_dict[restaurant]['popularity_rank'] = (
            sorted_popularity.index(restaurant) + 1)
        # Get combined score that is weighted more to favor rating than
        # popularity
        rest_dict[restaurant]['combined_score'] = (
            float(rest_dict[restaurant]['popularity_rank']) * 0.3
            + float(rest_dict[restaurant]['rating_rank']) * 0.7)
    # Sorts this combined score list and creates a ranking for it and saves
    # the restaurate ranking to the restaurant in the dictionary
    sorted_score = sorted(rest_dict, 
        key=lambda x: (rest_dict[x]['combined_score']))
    for restaurant in rest_dict:
        rest_dict[restaurant]['restaurate_rank'] = (
            sorted_score.index(restaurant) + 1)


def elasped_time(original_function):
    """Times functions for debug purposes """
    def wrapper(*args, **kwargs):
        start = time.time()
        result = original_function(*args, **kwargs)
        end = time.time()
        elapsed = end - start
        logging.debug(original_function.__name__
            + " took " + str(elapsed) + " seconds.")     
        return result   
    return wrapper
