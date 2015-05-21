#!/usr/bin/env python

import csv
import requests
import argparse
# import string
# import random
import logging

from rdflib import Graph, URIRef
from collections import defaultdict


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

handler = logging.FileHandler(filename='stat.log', mode='w', delay=True)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

log.addHandler(handler)
log.addHandler(console_handler)

cache = logging.getLogger('cache')
cache.setLevel(logging.INFO)
cache_handler = logging.FileHandler(filename='cache.log', mode='a', delay=True)
cache_handler.setLevel(logging.INFO)
cache.addHandler(cache_handler)

CACHE = "/Users/hoekstra/Dropbox/projects/designpatterns_stats/"
PATTERN2URL = '/Users/hoekstra/Dropbox/projects/designpatterns_stats/sources.csv'
RESOURCE2DOCUMENT = 'resource2document.csv'
RESOURCE2DOCUMENT_URL = 'http://index.lodlaundromat.org/get/r2d/'
PATTERN2DOCUMENT = 'pattern2document.csv'
PATTERN2DOCUMENT_STATS = 'pattern2document_stats.csv'
PROPERTYOCCURRENCES = 'property_occurrences.csv'


DOMAIN_RANGE_QUERY = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT ?domain ?property ?range WHERE {
  { OPTIONAL { ?property rdfs:domain ?domain . }
  	?property rdfs:range ?range . }
  UNION
  { ?property rdfs:domain ?domain .
	OPTIONAL { ?property rdfs:range ?range . } }
  UNION
  {
    ?domain rdfs:subClassOf|owl:equivalentClass ?restriction .
    ?restriction owl:onProperty ?property .
    OPTIONAL { ?restriction owl:someValuesFrom ?range . }
    OPTIONAL { ?restriction owl:allValuesFrom ?range . }
    OPTIONAL { ?restriction owl:hasValue ?range . }
    OPTIONAL { ?restriction owl:hasSelf "true"^^xsd:boolean . BIND(?domain as ?range)}
    OPTIONAL { ?restriction owl:onClass ?range . }
  }
} """


# Patterns to urls
p2u = {}
# Patterns to files
p2f = {}
# Resources to documents
r2d = {}
# Patterns to documents
p2d = defaultdict(set)


def get_stats(name):
    filename = '{}.csv'.format(name)

    try:
        with open(filename) as cachefile:
            cached_lines = cachefile.readlines()

        cached_stats = {key: int(value) for [key, value] in [l.split(';') for l in cached_lines]}
    except:
        cached_stats = {}

    stat_logger = logging.getLogger(name)
    stat_logger.setLevel(logging.INFO)
    stat_logger_handler = logging.FileHandler(filename=filename, mode='a', delay=True)
    stat_logger_handler.setLevel(logging.INFO)
    stat_logger.addHandler(stat_logger_handler)

    return cached_stats, stat_logger


def initialize_p2u():
    with open(PATTERN2URL, 'r') as f:
        reader = csv.reader(f, delimiter=';', quotechar='"')

        for l in reader:
            p2u[l[0]] = l[1]

            p2f[l[0]] = CACHE + l[1].replace('/', '_s_').replace(':', '_c_')


def initialize_r2d():
    with open(RESOURCE2DOCUMENT, 'r') as f:
        reader = csv.reader(f, delimiter=';', quotechar='"')

        for l in reader:
            r2d[l[0]] = eval(l[1])


def initialize_p2d():
    with open(PATTERN2DOCUMENT, 'r') as f:
        reader = csv.reader(f, delimiter=';', quotechar='"')

        for l in reader:
            p2d[l[0]] = eval(l[1])


def generate_r2d():
    visited = set()
    for source, url in p2u.items():
        log.info("Dataset: {}".format(url))
        filename = p2f[source]

        g = Graph()
        try:
            g.parse(filename, format='turtle')
        except Exception as e:
            log.error("Could not parse document: {}".format(filename))
            log.error(e)
            continue

        subjects = [s for s in list(g.subjects()) if isinstance(s, URIRef)]
        predicates = [p for p in list(g.predicates())]
        objects = [o for o in list(g.objects()) if isinstance(o, URIRef)]

        # Filter resources that are very (very) common to remove the
        # possibilities for false positives.
        all_resources = [r for r in subjects + predicates + objects if
                         not('www.w3.org' in str(r)) and
                         not('dbpedia.org' in str(r)) and
                         not('http://purl.org/dc' in str(r)) and
                         not('http://xmlns.com/foaf/0.1/' in str(r))]

        for s in all_resources:
            if s not in visited:
                log.debug(s)

                params = {'key': s}

                response = requests.get(RESOURCE2DOCUMENT_URL, params=params)

                datasets_string = response.content.strip()

                if len(datasets_string) > 0:
                    dataset_hashes = datasets_string.split(' ')

                    r2d[s] = dataset_hashes
                    p2d[url] = p2d[url].union(dataset_hashes)
                else:
                    r2d[s] = []
                visited.add(s)
            else:
                dataset_hashes = r2d[s]
                p2d[url] = p2d[url].union(dataset_hashes)

        log.info("P2D: {}".format(len(p2d[url])))

    save_r2d()
    save_p2d()
    save_p2d_stats()


def save_r2d():
    # Write everything to a file
    f = open(RESOURCE2DOCUMENT, 'w')
    for resource, document in r2d.items():
        f.write('"{}";"{}"\n'.format(resource, document))

    f.close()


def save_p2d():
    # Write everything to a file
    f = open(PATTERN2DOCUMENT, 'w')
    for pattern, document in p2d.items():
        f.write('"{}";"{}"\n'.format(pattern, document))

    f.close()


def save_po(po):
    # Write everything to a file
    f = open(PROPERTYOCCURRENCES, 'w')
    for url, count in po.items():
        f.write('"{}";"{}"\n'.format(url, count))

    f.close()


def save_p2d_stats():
    # Write everything to a file
    f = open(PATTERN2DOCUMENT_STATS, 'w')
    for pattern, documents in p2d.items():
        f.write('"{}";"{}"\n'.format(pattern, len(documents)))

    f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process design patterns')
    parser.add_argument('--init', dest='init', action='store_const',
                        const=True, default=False,
                        help='Initialize indexes from LOD Laundromat')

    args = parser.parse_args()

    log.info('Initializing mappings from patterns to urls')
    initialize_p2u()

    if args.init:
        log.info('Generating mapping from resources to documents')
        generate_r2d()
    else:
        log.info('Initializing mappings from file')
        initialize_r2d()
        initialize_p2d()

    log.info("Initialized...")
    property_occurrences = {}

    property_stats, property_statlogger = get_stats('property')
    pattern_stats, pattern_statlogger = get_stats('pattern')

    for source, url in p2u.items():
        if url in pattern_stats:
            log.info('Pattern {} was already visited'.format(url))
            continue

        log.info("Generalizing {}".format(url))

        filename = p2f[source]
        g = Graph()

        try:
            g.parse(filename, format='turtle')
        except Exception as e:
            log.error("Could not parse document: {}".format(filename))
            log.error(e)
            continue

        lodl_documents = p2d[url]

        # Start counting from 0, oh, smart!
        pattern_stats[url] = 0

        # This query returns the usage of properties in axioms (not all of them)
        results = g.query(DOMAIN_RANGE_QUERY)
        properties = set([str(p) for s, p, o in results])


        mapping = {}
        log.info("Anticipating occurrences in {} datasets.".format(len(lodl_documents)))
        for p in properties:
            log.debug("Property {}".format(p))
            if p in property_stats:
                log.debug("Property {} was already visited".format(p))
                # Add the known property stats count to the pattern stats
                # And do not log it... for obvious reasons.
                pattern_stats[url] += property_stats[p]
                continue

            # Start counting from 0, oh, smart!
            property_stats[p] = 0

            for document_hash in lodl_documents:
                log.debug("Checking for occurrences in dataset #{}".format(document_hash))
                ldf_url = 'http://ldf.lodlaundromat.org/{}'.format(document_hash)

                params = {'predicate': p}

                result = requests.get(ldf_url, params=params,
                                      headers={'Accept': 'application/json'})

                tpf = Graph()
                tpf.parse(data=result.content, format='json-ld')

                property_stats[p] += len(tpf)

            # Add the property to the cached list of visited properties
            # (writing using a logger)
            property_statlogger.info('{};{}'.format(p, property_stats[p]))
            # Add the property stats to the statistics for the pattern in which
            # it occurs
            pattern_stats[url] += property_stats[p]

        log.info("Found occurrences in {} datasets".format(pattern_stats[url]))
        # Add the pattern stats to the cached list of visited patterns
        pattern_statlogger.info('{};{}'.format(url, pattern_stats[url]))
