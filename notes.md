# Notes


Question:
* What constitutes the instantiation or usage of an Ontology Design Pattern?
  * The literal usage of the ODP in an ontology (i.e. it reappears in an ontology)
  * The usage of classes and properties in an instantiated dataset:
    1. properties from the ODP are used to relate resources in the dataset,
    2. classes are instantiated in the dataset.
    3. ...?
  * The usage of classes and properties in definitions in datasets:
    1. properties in the dataset are subsumed by ODP properties,
      - `<p,rdfs:subPropertyOf,odp_p>`
      - `<p,owl:propertyChainAxiom,(...,odp_p)>`
    2. properties in the datataset use ODP classes as domain or range
    3. classes are defined using properties from the ODP, or
      - `<restriction,owl:onProperty,odp_p>`
    4. classes are subsumed by classes from the ODP)


Distinguish between

* Data generated according to a design pattern
* The use of the design pattern itself:
  - Literal usage
  - Literal usage at QName level
  - Extension of the pattern
  - Reflection of the pattern (structural correspondence) 
    *This requires some abstract representation of the pattern, .*


### Subgraph Isomorphism

```python
from networkx.algorithms import isomorphism

G1 = nx.path_graph(4)
G2 = nx.path_graph(4)
GM = isomorphism.DiGraphMatcher(G1,G2)

GM.is_isomorphic()
GM.subgraph_is_isomorphic()
```

soft rules: partially true or true.
