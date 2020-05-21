from rdflib import Graph, Namespace, query, RDF
from nltk.corpus import wordnet as wn

g = Graph()

g.load("./data/own-pt.ttl", format="turtle")

skos = Namespace("http://www.w3.org/2004/02/skos/core#")
wnpt = Namespace("https://w3id.org/own-pt/wn30/schema/")
# 
sense_file = open('./wordnet/index.sense', 'w', encoding="utf-8")

synset_types = {wn.NOUN:1,wn.VERB:2,wn.ADJ:3,wn.ADV:4,wn.ADJ_SAT:5}

def process_synsets(rdf_class, pos):
    for synset,p,o in g.triples((None, RDF.type, wnpt[rdf_class])):
        for _, _,sense in g.triples((synset, wnpt.containsWordSense, None)):
            wordNumber = g.value(sense, wnpt.wordNumber, None)
            if wordNumber is None:
                try:
                    parts = g.qname(sense).split('-')
                    wordNumber = parts[-1]
                except:
                    wordNumber = "0"

            wordNumber = str(wordNumber).zfill(2)
            word_label = g.label(sense)
            prepared_word = "_".join(str(word_label.strip()).split(" ")).lower()
            offset = "-".join(g.qname(synset).split('-')[-2:])
            # pos = g.qname(synset).split('-')[-1]
            pos_index = synset_types[pos]
            synset_offset = g.qname(synset).split('-')[-2]
            ss = wn.of2ss(offset)
            lexname_index=None
            for lemma in ss.lemmas():
                lexname_index = lemma._lexname_index
                break
            # lemma%lex_sense:lex_filenum:lex_id:head_word:head_id
            sense_key = "{0}%{1}:{2}:{3}::".format(prepared_word,str(pos_index),str(lexname_index).zfill(2),wordNumber )
            # print(word_label, sense_key)
            # sense_key  synset_offset  sense_number  tag_cnt
            item = "{0} {1} {2} {3}".format(sense_key, synset_offset, str(int(wordNumber)), '0')
            print(item)
            sense_file.write(item+"\n")
process_synsets("NounSynset",'n')
process_synsets("VerbSynset",'v')
process_synsets("AdverbSynset",'r')
process_synsets("AdjectiveSynset",'a')
# process_synsets("AdjectiveSynset",'a')

# for s,p,o in g.triples((None, RDF.type, wnpt.WordSense)):
#     wordNumber = g.value(s, wnpt.wordNumber, None)
#     if wordNumber is None:
#         wordNumber = 0
#     wordNumber = str(wordNumber).zfill(2)
#     word_label = g.label(s)
#     prepared_word = "_".join(str(word_label.strip()).split(" ")).lower()
#     synset = g.value(None, wnpt.containsWordSense, s)
#     offset = "-".join(g.qname(synset).split('-')[-2:])
#     pos = g.qname(synset).split('-')[-1]
#     pos_index = synset_types[pos]
#     offset_ = g.qname(synset).split('-')[-2]

#     ss = wn.of2ss("09918248-n")
#     lexname_index=None
#     for lemma in ss.lemmas():
#         lexname_index = lemma._lexname_index
#         break
#     # lemma%lex_sense:lex_filenum:lex_id:head_word:head_id
#     sense_key = "{0}%{1}:{2}:{3}::".format(prepared_word,str(pos_index),str(lexname_index),wordNumber )
#     print(word_label, sense_key)

    # sense_key  synset_offset  sense_number  tag_cnt