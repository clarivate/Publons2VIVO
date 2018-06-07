"""
Basic Python client for Publons.
https://publons.com/api/v2/
"""

from itertools import izip_longest
import os
import requests
import logging
from datetime import datetime
from logging import handlers
from datetime import datetime
import argparse
import json
from rdflib import Literal, Graph, XSD, URIRef
from rdflib.namespace import Namespace
from namespace import (VIVO, VCARD, OBO, BIBO, FOAF, SKOS, D,
                                      RDFS, RDF, PUB)
import SPARQLWrapper
import namespace as ns
from api_fx import (vivo_api_query, uri_gen, create_vcard)

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
    academic_list = set()

    page = 1
    while True:
        r = get_r(BASE_URL, req)
        try:
            for person in r['results']:
                per_url = (person['ids']['api'].
                           replace('https://publons.com/api/v2/academic/', ''))
                academic_list.add(per_url[0:-1])
        except:
            print('Received invalid response')


        if r['next'] is not None:
            req = req + '&page={}'.format(page)
            page+=1
        else:
            break

    return(academic_list)


def get_academic_details(BASE_URL, id, d):
    req = 'academic/review/?academic={}&page=1'.format(id)
    academic_reviews = []

    page = 1
    while True:
        r = get_r(BASE_URL, req)
        try:
            for result in r['results']:
                review_url = {}
                review_url['id'] = result['ids']['academic']['id']
                review_url['url'] = result['ids']['academic']['url']
                review_url['date'] = result['date_reviewed']
                review_url['journal'] = result['journal']['name']
                review_url['journal_issn'] = result['journal']['ids']['issn']
                review_url['journal_eissn'] = result['journal']['ids']['eissn']

                academic_reviews.append(review_url)
        except:
            print('Received invalid response')


        if r['next'] is not None:
            req = req.replace('page={}'.format(page),'page={}'.format(page+1))
            page+=1
        else:
            break
    d[id]['reviews'] = academic_reviews
    return(d)


def get_academic_basic_info(BASE_URL, id, d):
    req = 'academic/{}'.format(id)
    r = get_r(BASE_URL, req)
    d[id] = {}
    try:
        d[id]['merit'] = r['merit']
        d[id]['name'] = r['publishing_name']
        d[id]['url'] = r['ids']['url']
        d[id]['id'] = r['ids']['id']
        d[id]['orcid'] = r['ids']['orcid']
        d[id]['pre'] = r['reviews']['pre']['count']
        d[id]['post'] = r['reviews']['post']['count']

    except:
        print('Received invalid response')

    return(d)


def gen_review_triples(per_uri, data, journals, g):
    for review in data['reviews']:
        journal_uri = None
        if 'journal_issn' in review and review['journal_issn']:
            if review['journal_issn'] in journals:
                journal_uri = URIRef(journals[review['journal_issn']])
                logger.debug('Matched journal via ISSN')
        elif 'journal_eissn' in review and review['journal_eissn']:
            if review['journal_eissn'] in journals:
                journal_uri = URIRef(journals[review['journal_eissn']])
                logger.debug('Matched journal via EISSN')
        if not journal_uri:
            logger.debug('Could not match journal, creating a new one')
            journal_uri = D[uri_gen('jrnl-')]
            g.add((journal_uri, RDF.type, BIBO.Journal))
            g.add((journal_uri, RDFS.label, Literal(review['journal'])))
            if 'journal_issn' in review and review['journal_issn']:
                g.add((journal_uri, BIBO.issn, Literal(review['journal_issn'])))
                journals[review['journal_issn']] = journal_uri
            if 'journal_eissn' in review and review['journal_eissn']:
                g.add((journal_uri, BIBO.eissn, Literal(review['journal_eissn'])))
                journals[review['journal_eissn']] = journal_uri

        rev_uri = 'review-{}'.format(review['id'])
        vcard_uri = 'review-vcard-{}'.format(review['id'])
        url_uri = 'review-url-{}'.format(review['id'])
        role_uri = 'reviewer-role-{}'.format(review['id'])
        g.add((D[rev_uri], PUB.reviewFor, journal_uri))
        g.add((journal_uri, PUB.reviewFor, D[rev_uri]))
        g.add((D[rev_uri], RDF.type, PUB.Review))
        g.add((D[rev_uri], RDFS.label, Literal('Review {}'.format(review['id']),
               datatype=XSD.string)))
        g.add((D[rev_uri], VIVO.contributingRole, D[role_uri]))
        g.add((D[role_uri], VIVO.roleContributesTo, D[rev_uri]))
        g.add((D[role_uri], RDF.type, VIVO.ReviewerRole))
        g.add((D[role_uri], OBO.RO_0000052, per_uri))
        g.add((per_uri, OBO.RO_0000053, D[role_uri]))
        g.add((D[rev_uri], OBO.ARG_2000028, D[vcard_uri]))
        g.add((D[vcard_uri], OBO.ARG_2000029, D[rev_uri]))
        g.add((D[vcard_uri], RDF.type, VCARD.Individual))
        g.add((D[vcard_uri], VCARD.hasURL, D[url_uri]))
        g.add((D[url_uri], RDF.type, VCARD.URL))
        g.add((D[url_uri], VCARD.url, Literal(review['url'])))
        if 'date' in review and review['date']:
            date_uri = 'review-date-{}'.format(review['id'])
            g.add((D[rev_uri], VIVO.dateTimeValue, D[date_uri]))
            g.add((D[date_uri], RDF.type, VIVO.DateTimeValue))
            g.add((D[date_uri], VIVO.dateTimePrecision, VIVO.yearPrecision))
            g.add((D[date_uri], VIVO.dateTime, Literal("{}".format(review['date']), datatype=XSD.year)))
    return (g, journals)


def get_people():
    # Let's try to match on ORCIDs
    query = ("PREFIX vivo: <"+VIVO+"> "
             "PREFIX foaf: <"+FOAF+"> "
             "SELECT ?per ?orcid "
             "WHERE { "
	         "?per a foaf:Person . "
             "?per vivo:orcidId ?orcid . "
             "} ")

    bindings = vivo_api_query(query)
    people = {}
    if bindings:
        for rec in bindings:
             if 'per' in rec:
                 uri = rec['per']['value']
                 orcid = rec['orcid']['value'].replace('http://orcid.org/',
                            '').replace('https://orcid.org/', '')
                 people[orcid] = uri
    log.debug(people)
    return people


def get_journals():
    # Let's try to match on ORCIDs
    query = ("PREFIX vivo: <"+VIVO+"> "
             "PREFIX bibo: <"+BIBO+"> "
             "SELECT ?journal ?issn ?eissn "
             "WHERE {{ "
	         "?journal a bibo:Journal . } "
             "UNION {?journal a bibo:Journal . "
             "?journal bibo:issn ?issn . } "
              "UNION {?journal a bibo:Journal . "
              "?journal bibo:eissn ?eissn . } "
             "} ")

    bindings = vivo_api_query(query)
    journals = {}
    if bindings:
        for rec in bindings:
            if 'journal' in rec:
                uri = rec['journal']['value']
                if 'issn' in rec:
                    issn = rec['issn']['value']
                    journals[issn] = uri
                if 'eissn' in rec:
                    eissn = rec['eissn']['value']
                    journals[eissn] = uri
    log.debug(journals)
    return journals


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-o", "--organization", help="Pull data for all "
                        "researchers affiliated with this organization.")
    group.add_argument("-i", "--ids", help="The ORCID or Publons IDs to "
                       "search in csv format")

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
people = get_people()
journals = get_journals()

if args.organization:
    academics = get_academics(BASE_URL, args.organization)
    log.debug(academics)
elif args.ids: # Orgs or IDs required by the arg parser
    academics = args.ids.split(',')
    log.debug(academics)

# Instantiate a graph and namespace
g = Graph(namespace_manager=ns.ns_manager)

d = {}
for id in academics:
    d = get_academic_basic_info(BASE_URL, id, d)
    d = get_academic_details(BASE_URL, id, d)


# Now we have a subset of data we can work with
for publons_profile in d:
    log.debug(publons_profile)
    if 'orcid' in d[publons_profile] and d[publons_profile]['orcid']:
        orcid = d[publons_profile]['orcid']

        if orcid in people:
            per_uri = URIRef(people[orcid])
            g += gcard
            log.debug('Matched record with ORCID {} in VIVO'.format(orcid))
        else:
            (per_uri, gcard) = create_vcard(d[publons_profile]['name'])
            log.debug('ORCID {} not found in VIVO'.format(orcid))
    else:
        (per_uri, gcard) = create_vcard(d[publons_profile]['name'])
        g += gcard
    #print(d[publons_profile])
    (g_rev, journals) = gen_review_triples(per_uri, d[publons_profile], journals, g)
    g+=g_rev

timestamp = str(datetime.now())[:-7]
if len(g) > 0:
    try:
        with open("rdf/publons-"+timestamp+"-in.ttl", "w") as f:
            f.write(g.serialize(format=args.format))
            log.info('Wrote RDF to rdf/publons-' + timestamp +
                     '-in.ttl in ' + args.format + ' format.')
    except IOError:
        # Handle the error.
        log.exception("Failed to write RDF file. "
                      "Does a directory named 'rdf' exist?")
        log.exception("The following RDF was not saved: \n" +
                      g.serialize(format=args.format))
else:
    log.info('No triples to INSERT.')
