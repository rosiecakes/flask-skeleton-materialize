# -*- coding: utf-8 -*-

import datetime
import logging
import sqlite3
from flask import g

try:
    from utility import *
except:
    from .utility import scrub_tablename

from project.server import config, app
# from restaurate import app


# def init_db():
#     with closing(connect_db()) as db:
#         with app.open_resource('schema.sql', mode='r') as f:
#             db.cursor().executescript(f.read())
#         db.commit()


def connect_db():
    return sqlite3.connect(config.DATABASE_NAME)


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


def check_table_exists(location):
    c = g.db.cursor()
    c.execute("""
        SELECT count(*)
        FROM sqlite_master
        WHERE type='table' AND name='{0}'
        """.format(scrub_tablename(location)))
    if c.fetchone()[0] == 1:
        c.close()
        return True
    c.close()
    return False


def time_stamp_exists(location):
    c = g.db.cursor()
    c.execute("""
        SELECT timestamp FROM {0}
        """.format(scrub_tablename(location)))
    if c.fetchone() != None:
        c.close()
        return True
    c.close()
    return False


def check_time_stamp(location):
    c = g.db.cursor()
    c.execute("""
        SELECT timestamp FROM {0}
        """.format(scrub_tablename(location)))

    tableDate = datetime.datetime.strptime(
        c.fetchone()[0], "%Y-%m-%d %H:%M:%S.%f")
    difference = abs(datetime.datetime.utcnow() - tableDate).days
    if difference < 30:
        c.close()
        return True
    c.close()
    return False


def get_table(location, rest_dict):
    c = g.db.cursor()
    logging.debug("Reading results from database...")
    for row in c.execute(
                'SELECT * FROM {0} ORDER BY restaurate_rank ASC'.format(
                    scrub_tablename(location))):
            # logging.debug(row)
            rest_dict[row[1]] = {}
            rest_dict[row[1]]['restaurate_rank'] = row[0]
            rest_dict[row[1]]['average_rating'] = row[2]
            rest_dict[row[1]]['zomato_rating'] = row[3]
            rest_dict[row[1]]['google_rating'] = row[4]
            rest_dict[row[1]]['zomato_review_count'] = row[5]
            rest_dict[row[1]]['zomato_price'] = row[6]
            rest_dict[row[1]]['cuisines'] = row[7]
            rest_dict[row[1]]['timestamp'] = row[8]
    # logging.debug(pp(rest_dict))
    c.close()
    return rest_dict


def delete_table(location):
    c = g.db.cursor()
    logging.debug("Timestamp invalid, removing old table")
    c.execute("DROP TABLE {0}".format(scrub_tablename(location)))
    # Save (commit) the changes
    g.db.commit()
    c.close()


def create_table(location, rest_dict):
    c = g.db.cursor()
    timestamp = datetime.datetime.utcnow()
    logging.debug("Getting data and creating new table")
    # Create table
    c.execute('''CREATE TABLE {0}
                 (restaurate_rank integer,
                 restaurant text,
                 average_rating real,
                 zomato_rating real,
                 google_rating real,
                 zomato_review_count integer,
                 zomato_price text,
                 cuisines text,
                 timestamp text)'''.format(scrub_tablename(location)))

    # Insert a row of data
    for restaurant in rest_dict:
        restaurant_info = \
        (rest_dict[restaurant]['restaurate_rank'],
         restaurant, \
         rest_dict[restaurant]['average_rating'], \
         rest_dict[restaurant]['zomato_rating'], \
         rest_dict[restaurant]['google_rating'], \
         rest_dict[restaurant]['zomato_review_count'], \
         rest_dict[restaurant]['zomato_price'], \
         rest_dict[restaurant]['cuisines'], \
         timestamp)
        c.execute("INSERT INTO {0} VALUES (?,?,?,?,?,?,?,?,?)".format(
            scrub_tablename(location)), restaurant_info)

    # Save (commit) the changes
    g.db.commit()
    c.close()
