from rdflib import Graph, Namespace, OWL, RDF, RDFS, URIRef
from glob import glob
import os

PATH = "/Users/hoekstra/Dropbox/projects/designpatterns_stats/*.owl"
DESTINATION = "/Users/hoekstra/projects/designpatterns/stripped"

for f in glob(PATH):
    (_, target_name) = os.path.split(f)

    g = Graph()
    g.parse(f, format='turtle')
    print g.serialize(format='turtle')
    g.remove((None, None, OWL['AnnotationProperty']))
    print g.serialize(format='turtle')
    print list(g.all_nodes())
    annotations = [uri for uri in list(g.all_nodes()) if isinstance(uri, URIRef) and 'http://www.ontologydesignpatterns.org/schemas/cpannotationschema.owl#' in str(uri)]
    print annotations
    break
