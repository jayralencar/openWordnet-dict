from rdflib import Graph, Namespace, query, RDF, URIRef
from nltk.corpus import wordnet as wn
import requests
import json
from freeling import Freeling
from html import unescape
import io
import sys 

sys.setrecursionlimit(10**6) 

fl = Freeling()
g = Graph()

g.load("./data/own-pt.ttl", format="turtle")
synset_types = {wn.NOUN:1,wn.VERB:2,wn.ADJ:3,wn.ADV:4,wn.ADJ_SAT:5}
pos_tags = [wn.ADJ, wn.VERB, wn.NOUN, wn.ADV, wn.ADJ_SAT]
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
wnpt = Namespace("https://w3id.org/own-pt/wn30/schema/")
instances = Namespace("https://w3id.org/own-pt/wn30-pt/instances/")

nltk_wordnet_data = "/home/jayr/nltk_data/corpora/wordnet"
sense_file = open('./wordnet/index.sense', 'w', encoding="utf-8")

pos_mapping = {"v":"verb", "n":"noun", "a":"adj", "s":"adj", "r":"adv"}

pwn_to_ownpt = open("./wordnet/pwn_to_ownpt.txt",'w')

files = [
    "noun",
    "verb",
    "adj",
    "adv"
]

offset_mapping = {
    "noun":{},
    "verb":{},
    "adj": {},
    "adv": {}
}

new_offset_lists = {
    "noun":[],
    "verb":[],
    "adj": [],
    "adv": []
}

new_lines = {
    "noun":{},
    "verb":{},
    "adj": {},
    "adv": {}
}

lemmas = {
    "noun":{},
    "verb":{},
    "adj": {},
    "adv": {}
}

def insert_sense_index(lemma, offset, pos,lexname_index):
    sense_key = "{0}%{1}:{2}:{3}::".format(lemma,synset_types[pos],str(lexname_index).zfill(2),"01")
    item = "{0} {1} {2} {3}".format(sense_key, offset, '01', '0')
    sense_file.write(item+"\n")

def proceed_words(prepared_word, new_offset, symbols, data_items):
    insert_sense_index(prepared_word,new_offset,data_items[2], data_items[1])
    pos_name = pos_mapping[data_items[2]]
    if prepared_word not in lemmas[pos_name]:
        lemmas[pos_name][prepared_word] = {
            "symbols": [],
            "synsets": [],
            "pos": data_items[2]
        }
    lemmas[pos_name][prepared_word]['synsets'].append(new_offset)
    lemmas[pos_name][prepared_word]['symbols'] += list(set(lemmas[pos_name][prepared_word]['symbols'] + symbols))

def get_translation(gloss, exactly=False):
    res = requests.get(
        'https://mymemory.translated.net/api/ajaxfetch?q='+gloss+'&langpair=en|pt-br&mtonly=1')
    result = json.loads(res.text)
    if result['responseStatus'] == 429:
        # raise Exception('Estourou o limite!')
        return gloss
    if exactly:
        for mat in result['matches']:
            if mat['segment'].lower() == gloss:
                return mat['translation']
    else:
        if len(result["matches"]) > 0:
            return result['matches'][0]['translation']
    return gloss

initial_offset = 1100

def save_synset(offset, line):
    _data, gloss = line.split("|")
    data_items = _data.strip().split(" ")
    pos_name = pos_mapping[data_items[2]]
    if offset in offset_mapping[pos_name]:
        return offset_mapping[pos_name][offset]
    else:
        if len(new_offset_lists[pos_name]) == 0:
            new_offset = initial_offset
        else:
            new_offset = int(new_offset_lists[pos_name][-1]) + len(new_lines[pos_name][new_offset_lists[pos_name][-1]].encode("utf-8"))
        new_offset = str(new_offset).zfill(8)
        idx = [i for i in range(len(data_items))  if len(data_items[i]) == 3 and data_items[i].isnumeric()][0]
        rdf_offset = "synset-{0}-{1}".format(data_items[0], data_items[2])

        synset = URIRef(instances[rdf_offset])

        pt_gloss = g.value(synset, wnpt.gloss, None)
        if pt_gloss is None:
            pt_gloss = get_translation(gloss.rstrip())
        else:
            pt_gloss = pt_gloss.value

        words = []
        symbols = list(set([item for item in data_items[idx:] if not item.isnumeric() and item not in pos_tags]))
        for _, _, sense in g.triples((synset, wnpt.containsWordSense, None)):
            word_label = g.label(sense)
            prepared_word = "_".join(str(word_label.strip()).split(" ")).lower()
            proceed_words(prepared_word, new_offset, symbols, data_items)
            words.append(prepared_word)

        if len(words) == 0:
            for item in data_items[4:idx]:
                if not item.isnumeric():
                    translated = get_translation(" ".join(item.split("_")), exactly=True)
                    prepared_word = "_".join(translated.split(" ")).lower()
                    proceed_words(prepared_word, new_offset, symbols, data_items)
                    words.append(prepared_word)
        pt_gloss += "\n"
        part1 = [new_offset]+data_items[1:3]+[str(len(words)).zfill(2)]
        part2 = []
        for word in words:
            part2.append(word)
            part2.append("0")
        part3 = data_items[idx:]
        new_data_line = "{0} | {1}".format(" ".join(part1+part2+part3), unescape(pt_gloss))
        print(new_data_line)

        offset_mapping[pos_name][offset] = new_offset
        new_offset_lists[pos_name].append(new_offset)
        new_lines[pos_name][new_offset] = new_data_line

        
        if len(data_items[idx:]) > 0:
            relations = []
            for _i in range(idx, len(data_items)):
                if len(data_items[_i]) == 8:
                    item_file = open("{0}/data.{1}".format(nltk_wordnet_data, pos_mapping[data_items[_i+1]]), "r")
                    item_file.seek(int(data_items[_i]))
                    n_of = save_synset(data_items[_i], item_file.readline())
                    relations.append(n_of)
                    item_file.close()
                else:
                    relations.append(data_items[_i])
            new_data_line = "{0} | {1}".format(" ".join(part1+part2+relations), unescape(pt_gloss))
            # print(new_data_line)
            new_lines[pos_name][new_offset] = new_data_line
        return new_offset

for file_ in files:
    origin_file = open("{0}/data.{1}".format(nltk_wordnet_data, file_), "r")
    for line in origin_file.readlines():
        if not line.startswith(' '):
            #  _data, gloss = line.split("|")
            # data_items = _data.strip().split(" ")
            offset = line.split(" ")[0]
            save_synset(offset, line)
            # break

for pos_name in new_offset_lists:
    destination_file = open("{0}/data.{1}".format("./wordnet", pos_name),"a", encoding="utf-8")
    for offset in new_offset_lists[pos_name]:
        destination_file.write(new_lines[pos_name][offset])
    destination_file.close()

for pos_name in lemmas:
    indx_file = open("./wordnet/index.{0}".format(pos_name),'w', encoding="utf-8")
    exec_file = open('./wordnet/{0}.exc'.format(pos_name), 'w', encoding="utf-8")
    for lemma in lemmas[pos_name]:
        item = lemmas[pos_name][lemma]
        # 0lemma  1pos  2synset_cnt  3p_cnt  4[ptr_symbol...]  5sense_cnt  6tagsense_cnt   7synset_offset  [synset_offset...] 
        insert_line = "{0} {1} {2} {3} {4} {5} 0 {6}".format(lemma, item['pos'],len(item['synsets']),len(item['symbols']), " ".join(item['symbols']),len(item['synsets']), " ".join(item['synsets']))
        indx_file.write(insert_line+"\n")
        forms = fl.forms(lemma, str(item['pos']).upper())
        for form in forms:
            exec_file.write(form+" "+lemma+"\n")
