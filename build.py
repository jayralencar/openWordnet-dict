from rdflib import Graph, Namespace, query, RDF

g_ownpt = Graph()

g_ownpt.load("./data/own-pt.ttl", format="turtle")

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
wnpt = Namespace("https://w3id.org/own-pt/wn30/schema/")