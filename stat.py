import csv
import requests
import argparse
import string
import random

from rdflib import Graph, URIRef
from collections import defaultdict


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
        print "Dataset:", url
        filename = p2f[source]

        g = Graph()
        try:
            g.parse(filename, format='turtle')
        except Exception as e:
            print "Could not parse document: ", filename
            print e
            continue

        subjects = [s for s in list(g.subjects()) if isinstance(s, URIRef)]
        predicates = [p for p in list(g.predicates())]
        objects = [o for o in list(g.objects()) if isinstance(o, URIRef)]

        all_resources = [r for r in subjects + predicates + objects if
                         not('www.w3.org' in str(r)) and
                         not('dbpedia.org' in str(r)) and
                         not('http://purl.org/dc' in str(r)) and
                         not('http://xmlns.com/foaf/0.1/' in str(r))]

        for s in all_resources:
            if s not in visited:
                print s

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

        print "P2D: ", len(p2d[url])

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

    initialize_p2u()
    if args.init:
        generate_r2d()
    else:
        initialize_r2d()
        initialize_p2d()

    print "Initialized..."

    property_occurrences = {}
    for source, url in p2u.items():
        print "Generalizing {}".format(url)

        filename = p2f[source]
        g = Graph()

        try:
            g.parse(filename, format='turtle')
        except Exception as e:
            print "Could not parse document: ", filename
            print e
            continue

        lodl_documents = p2d[url]

        # Start counting from 0, oh, smart!
        property_occurrences[url] = 0

        results = g.query(DOMAIN_RANGE_QUERY)

        mapping = {}

        print "Expecting occurrences in {} datasets.".format(len(lodl_documents))
        properties = set([p for s, p, o in results])
        for p in properties:
            print "Property {}".format(p)

            for document_hash in lodl_documents:
                ldf_url = 'http://ldf.lodlaundromat.org/{}'.format(document_hash)

                params = {'predicate': str(p)}

                result = requests.get(ldf_url, params=params,
                                      headers={'Accept': 'application/json'})

                tpf = Graph()
                tpf.parse(data=result.content, format='json-ld')

                property_occurrences[url] += len(tpf)

    save_po(property_occurrences)
