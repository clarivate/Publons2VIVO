"""
Basic Python client for Publons.
https://publons.com/api/v2/
"""

from itertools import izip_longest
import os
import requests
import logging
from logging import handlers
from datetime import datetime
import argparse

try:
    USER = os.environ['PUBLONS_USER']
    PASSWORD = os.environ['PUBLONS_PASSWORD']
except KeyError:
    raise Exception("Unable to read PUBLONS_USER and PUBLONS_PASSWORD environment variables.")

BASE_URL = "https://publons.com/api/v2/"

def get_token(BASE_URL):
    data = {"username": USER, "password": PASSWORD}
    r = requests.post(BASE_URL + 'token/', data=data)
    try:
        r = r.json()
        token = r['token']
    except:
        print("There was an error retrieving the token, sorry...")

    os.environ['PUBLONS_TOKEN'] = token


def get_r(BASE_URL, req):
    while True:
        if 'PUBLONS_TOKEN' not in os.environ:
            get_token(BASE_URL)
        token = os.environ['PUBLONS_TOKEN']
        headers = {'Authorization': 'Token ' + token, 'Content-Type': 'application/json'}
        r = requests.get(BASE_URL + req, headers=headers)
        if r.status_code != 200:
            raise Exception("Publons returned an error:\n" + r.text)
        try:
            r = r.json()
            if "detail" in r:
                if (r['detail'] == 'Invalid token.'):
                    get_token(BASE_URL)
            else:
                return r
        except:
            print('There was an error communiating with the Publons API')


def get_academics(BASE_URL, org):
    req = 'academic/?institution={}'.format(org)
    academic_list = []

    page = 1
    while True:
        r = get_r(BASE_URL, req)
        try:
            for person in r['results']:
                per_url = (person['ids']['api'].
                           replace('https://publons.com/api/v2/academic/', ''))
                academic_list.append(per_url)
        except:
            print('Received invalid response')


        if r['next'] is not None:
            req = req + '&page={}'.format(page)
            page+=1
        else:
            break

    return(academic_list)


def get_academic_details(BASE_URL, id, d):
    req = 'academic/review/?academic={}'.format(id)
    academic_reviews = []

    page = 1
    while True:
        r = get_r(BASE_URL, req)
        try:
            for result in r['results']:
                review_url = result['ids']['url']
                academic_reviews.append(review_url)
        except:
            print('Received invalid response')


        if r['next'] is not None:
            req = req + '&page={}'.format(page)
            page+=1
        else:
            break

    return(academic_reviews)


def get_academic_basic_info(BASE_URL, id, d):
    req = 'academic/{}'.format(id)
    r = get_r(BASE_URL, req)
    d[id] = {}
    try:
        d[id]['merit'] = r['merit']
        d[id]['pre'] = r['reviews']['pre']['count']
        d[id]['post'] = r['reviews']['post']['count']

    except:
        print('Received invalid response')

    return(d)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-o", "--organization", help="Pull data for all "
                        "researchers affiliated with this organization.")
    group.add_argument("-i", "--ids", help="The ORCID or Publons ID to search")

    parser.add_argument("--api", default=False, dest="use_api",
                        action="store_true", help="Send the newly created "
                        "triples to VIVO using the update API. Note, there "
                        "is no undo button! You have been warned!")
    parser.add_argument("-a", "--auto", default=False, dest="auto_mode",
                        action="store_true", help="Run in auto mode. "
                        "Unknown organizations and people will automatically "
                        "be created instead of asking the user for input.")
    parser.add_argument("-f", "--format", default="turtle", choices=["xml",
                        "n3", "turtle", "nt", "pretty-xml", "trix"], help="The"
                        " RDF format for serializing. Default is turtle.")

    parser.add_argument("--debug", action="store_true", help="Set logging "
                        "level to DEBUG.")

    # Parse
    args = parser.parse_args()

# Set up logging to file and console
LOG_FILENAME = 'logs/publons-update.log'
LOG_FORMAT = '%(asctime)s - [%(levelname)s] - %(message)s'
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
if args.debug:
    LOGGING_LEVEL = logging.DEBUG
    logging.getLogger("requests").setLevel(logging.DEBUG)
else:
    LOGGING_LEVEL = logging.INFO
    logging.getLogger("requests").setLevel(logging.WARNING)

# Create console handler and set level
handler = logging.StreamHandler()
handler.setLevel(LOGGING_LEVEL)
formatter = logging.Formatter(LOG_FORMAT)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Create error file handler and set level
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=5000000,
                                               backupCount=5, encoding=None,
                                               delay=0)
handler.setLevel(LOGGING_LEVEL)
formatter = logging.Formatter(LOG_FORMAT)
handler.setFormatter(formatter)
logger.addHandler(handler)

log = logging.getLogger(__name__)

# Start the work
if args.organization:
    academics = get_academics(BASE_URL, args.organization)
    log.debug(academics)
else:
    academics = args.ids.split(',')
    log.debug(academics)

d = {}
for id in academics:
    d = get_academic_basic_info(BASE_URL, id, d)
    d = get_academic_details(BASE_URL, id, d)
