from bs4 import BeautifulSoup
import requests

# This is a manually generate list of pages that list design patterns
urls = ['http://ontologydesignpatterns.org/wiki/Submissions:ContentOPs','http://ontologydesignpatterns.org/wiki/Submissions:ReengineeringODPs','http://ontologydesignpatterns.org/wiki/Submissions:AlignmentODPs','http://ontologydesignpatterns.org/wiki/Submissions:LogicalODPs','http://ontologydesignpatterns.org/wiki/Submissions:ArchitecturalODPs','http://ontologydesignpatterns.org/wiki/Submissions:LexicoSyntacticODPs']

# Scrape each of these pages for design pattern urls
pattern_urls = []

for url in urls:
    response = requests.get(url)

    soup = BeautifulSoup(response.content)

    try :
        rows = soup.find_all('table')[1].find_all('tr')
    except:
        print "Problem with {}, no second table".format(url)
        rows = soup.find_all('table')[0].find_all('tr')

    # Loop through rows, skipping the header
    for r in rows[1:]:
        # First td in every tr
        # Add the value of 'href' to the list of pattern urls
        purl = r.td.a['href']
        print "Adding {}".format(purl)
        pattern_urls.append(purl)


# Get all design patterns
sources = {}

for purl in pattern_urls:
    purl = 'http://ontologydesignpatterns.org{}'.format(purl)

    response = requests.get(purl)

    soup = BeautifulSoup(response.content)

    ths = soup.find_all('table')[1].find_all('th')

    for th in ths:
        if th.string.strip() == 'Reusable OWL Building Block:':
            try :
                source_url = th.next_sibling.a.string.strip()
            except :
                source_url = th.next_sibling.string.strip()
            sources[purl] = source_url

from rdflib import Graph
from rdflib.namespace import OWL
from collections import defaultdict

print url


## Get the imported ontologies from the design patterns
additional_sources = defaultdict(list)

for source,url in sources.items():
    print "Loading {}".format(url)
    g = Graph()

    try:
        g.parse(url,format='xml')
    except:
        print "Could not parse {}".format(url)
        continue

    for s,p,o in g.triples((None,OWL['imports'],None)):
        if o != URIRef('http://www.ontologydesignpatterns.org/schemas/cpannotationschema.owl'):
            print "Adding {} to list".format(o)
            additional_sources[o].append(url)

    f = open(url.replace('/','_s_').replace(':','_c_'),'w')

    g.serialize(f,format='turtle')


# Write everything to a file
f = open('sources.csv','w')
for source, url in sources.items():
    f.write('"{}";"{}"\n'.format(source, url))

f.close()


f = open('additional_sources.csv','w')
for source, urls in additional_sources.items():
    for url in urls:
        f.write('"{}";"{}"\n'.format(source, url))

f.close()
