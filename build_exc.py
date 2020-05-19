from rdflib import Graph, Namespace, query, RDF
from freeling import Freeling

g = Graph()

fl = Freeling()

g.load("./data/own-pt.ttl", format="turtle")

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
wnpt = Namespace("https://w3id.org/own-pt/wn30/schema/")

adj = open('./wordnet/adj.exc', 'w', encoding="utf-8")
adv = open('./wordnet/adv.exc', 'w', encoding="utf-8")
noun = open('./wordnet/noun.exc', 'w', encoding="utf-8")
verb = open('./wordnet/verb.exc', 'w', encoding="utf-8")

for s,p,o in g.triples((None, RDF.type, wnpt.WordSense)):
    word = g.value(s, wnpt.word, None)
    
    word_label = g.label(s)

    synset = g.value(None, wnpt.containsWordSense, s)
    # print(word_label.value)
    pos = g.qname(synset).split('-')[-1]
    if word_label is not None:
        prepared_word = "_".join(str(word_label).split(" ")).lower()
        print(prepared_word)
        forms = fl.forms(prepared_word, str(pos).upper())
        for form in forms:
            if str(pos) == 'n':
                noun.write(form+" "+prepared_word+"\n")
            elif str(pos) == 'v':
                verb.write(form+" "+prepared_word+"\n")
            elif str(pos) == 'r':
                adv.write(form+" "+prepared_word+"\n")
            elif str(pos) in ['a','s']:
                adj.write(form+" "+prepared_word+"\n")

adv.close()
adj.close()
verb.close()
noun.close()