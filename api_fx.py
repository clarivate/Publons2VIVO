import requests
import logging
import os
import random
from rdflib import URIRef, Graph, Literal
from nameparser import HumanName
from namespace import D, VCARD, RDF, VIVO

# Define the VIVO store
try:
    API_URL = os.environ['VIVO_URL'] + '/api/sparqlQuery'
    UPDATE_URL = os.environ['VIVO_URL'] + '/api/sparqlUpdate'
    EMAIL = os.environ['VIVO_EMAIL'],
    PASSWORD = os.environ['VIVO_PASSWORD']
    NAMESPACE = os.environ['DATA_NAMESPACE']
except KeyError:
    raise Exception("Unable to read VIVO credentials in environment variables.")

# Generic query
def vivo_api_query(query):
    while True:
        payload = {'email': EMAIL, 'password': PASSWORD, 'query': ''+query}
        headers = {'Accept': 'application/sparql-results+json'}
        logging.debug(query)
        r = requests.post(API_URL, params=payload, headers=headers)
        try:
            json = r.json()
            bindings = json["results"]["bindings"]
        except ValueError:
            logging.exception(query)
            logging.exception("Nothing returned from query API. "
                              "Ensure your credentials and API url are set "
                              "correctly in your environment variables.")
            bindings = None
        return bindings

# Create unique URIs
def uri_gen(prefix, graph=None):
    while True:
        vivouri = prefix + str(random.randint(100000, 999999))
        payload = {'email': EMAIL, 'password': PASSWORD, 'query': 'ASK WHERE '
                   '{ <' + NAMESPACE + vivouri + '> ?p ?o . } '}
        r = requests.post(API_URL, params=payload)
        exists = r.text

        if graph:
            for s, p, o in graph:
                if (URIRef(NAMESPACE+vivouri), p, o) in graph:
                    exists = 'true'
                    logging.info('Determined that new uri ' + vivouri +
                                 'already exists in local database, trying '
                                 'again.')

        if exists == 'false':
            logging.debug('Determined that new uri ' + vivouri +
                          ' does not exist in database.')
            return vivouri
            break

        if exists == 'true':
            logging.debug('Determined that new uri ' + vivouri +
                          ' already exists in database, trying again.')

        else:
            logging.error('Unexpected response from VIVO Query API. Check '
                          'your credentials and API url in api_fx.py.')
            raise RuntimeError('URI generation failed. See log for details.')


def create_vcard(name):
    g = Graph()
    (per_uri, name_uri) = uri_gen('vcard-'), uri_gen('vcard-name-')
    name = HumanName(name)
    g.add((D[name_uri], VCARD.givenName, Literal(name.first)))
    g.add((D[name_uri], VCARD.familyName, Literal(name.last)))
    if name.middle != "":
        g.add((D[name_uri], VIVO.middleName, Literal(name.middle)))
    g.add((D[per_uri], RDF.type, VCARD.Individual))
    g.add((D[per_uri], VCARD.hasName, D[name_uri]))
    g.add((D[name_uri], RDF.type, VCARD.Name))

    return D[per_uri], g
