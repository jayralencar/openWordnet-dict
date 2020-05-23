from rdflib import Graph, Namespace, query, RDF, URIRef
from nltk.corpus import wordnet as wn
import requests
import json
from freeling import Freeling
from html import unescape
import io
import sqlite3
import datetime

connection = sqlite3.connect("./data/mapping.db")

def insert_mapping(pwn, new_offset, pos):
    cursor = connection.cursor()
    cursor.execute("INSERT INTO mapping (pwn, new_offset, pos) VALUES (?,?,?)",(int(pwn), int(new_offset), pos,))
    cursor.close()

def offset_processed(pwn, pos):
    t1 = datetime.datetime.now()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM mapping WHERE pwn = ? and pos = ?",(int(pwn),pos,))
    item = cursor.fetchone()
    cursor.close()
    connection.commit()
    t2 = datetime.datetime.now()
    print("TEST", t2-t1)
    return item is not None

nltk_wordnet_data = "/home/jayr/nltk_data/corpora/wordnet"
fl = Freeling()
g = Graph()

g.load("./data/own-pt.ttl", format="turtle")
synset_types = {wn.NOUN:1,wn.VERB:2,wn.ADJ:3,wn.ADV:4,wn.ADJ_SAT:5}
pos_tags = [wn.ADJ, wn.VERB, wn.NOUN, wn.ADV, wn.ADJ_SAT]
skos = Namespace("http://www.w3.org/2004/02/skos/core#")
wnpt = Namespace("https://w3id.org/own-pt/wn30/schema/")
instances = Namespace("https://w3id.org/own-pt/wn30-pt/instances/")
# synset_offset  lex_filenum  ss_type  w_cnt  word  lex_id  [word  lex_id...]  p_cnt  [ptr...]  [frames...]  |   gloss 
sense_file = open('./wordnet/index.sense', 'w', encoding="utf-8")

pwn_to_ownpt = {
    "noun":open("./wordnet/pwn_to_ownpt.noun",'w', encoding="utf-8"),
    "verb":open("./wordnet/pwn_to_ownpt.verb",'w', encoding="utf-8"),
    "adv":open("./wordnet/pwn_to_ownpt.adv",'w', encoding="utf-8"),
    "adj":open("./wordnet/pwn_to_ownpt.adj",'w', encoding="utf-8"),
}


files = [
    # "noun",
    "verb",
    "adj",
    "adv"
]

def get_translation(gloss, exactly=False):
    try:
        res = requests.get('https://api.mymemory.translated.net/get?q='+gloss+'&langpair=en|pt-br')
    except:
        return gloss
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

def insert_sense_index(lemma, offset, pos,lexname_index):
    
    sense_key = "{0}%{1}:{2}:{3}::".format(lemma,synset_types[pos],str(lexname_index).zfill(2),"01")
    item = "{0} {1} {2} {3}".format(sense_key, offset, '01', '0')
    sense_file.write(item+"\n")


for file_ in files:
    origin_file = open("{0}/data.{1}".format(nltk_wordnet_data, file_), "r")
    destination_file = open("{0}/temp_data.{1}".format("./wordnet", file_),"a", encoding="utf-8")
    destination_file.seek(0,io.SEEK_END)
    lemmas = {}
    for line in origin_file.readlines():
        if not line.startswith(' '):
            t_1 = datetime.datetime.now()
            _data, gloss = line.split("|")
            data_items = _data.strip().split(" ")
            if not offset_processed(data_items[0], file_):
                offset = "synset-{0}-{1}".format(data_items[0], data_items[2])
                new_offset = str(destination_file.tell()).zfill(8)

                # pwn_to_ownpt[file_].write("{0} {1}\n".format(data_items[0],new_offset))
                t1 = datetime.datetime.now()
                
                t2 = datetime.datetime.now()
                print("INSERT ", t2-t1)
                idx = [i for i in range(len(data_items))  if len(data_items[i]) == 3 and data_items[i].isnumeric()][0]
                synset = URIRef(instances[offset])

                pt_gloss = g.value(synset, wnpt.gloss, None)
                if pt_gloss is None:
                    pt_gloss = get_translation(gloss.rstrip())
                else:
                    pt_gloss = pt_gloss.value
                    pt_gloss = " ".join(pt_gloss.splitlines())
                pt_gloss = " ".join(pt_gloss.splitlines())
                
                words = []
                symbols = list(set([item for item in data_items[idx:] if not item.isnumeric() and item not in pos_tags]))
                t1 = datetime.datetime.now()
                for _, _, sense in g.triples((synset, wnpt.containsWordSense, None)):
                    word_label = g.label(sense)
                    prepared_word = "_".join(str(word_label.strip()).split(" ")).lower()
                    insert_sense_index(prepared_word,new_offset,data_items[2], data_items[1])
                    if prepared_word not in lemmas:
                        lemmas[prepared_word] = {
                            "symbols": [],
                            "synsets": [],
                            "pos": data_items[2]
                        }
                    lemmas[prepared_word]['synsets'].append(new_offset)
                    lemmas[prepared_word]['symbols'] += symbols
                    words.append(prepared_word)
                
                if len(words) == 0:
                    for item in data_items[4:idx]:
                        if not item.isnumeric():
                            # translated = get_translation(" ".join(item.split("_")), exactly=True)
                            # prepared_word = "_".join(translated.split(" ")).lower()
                            prepared_word = item
                            insert_sense_index(prepared_word,new_offset,data_items[2], data_items[1])
                            if prepared_word not in lemmas:
                                lemmas[prepared_word] = {
                                    "symbols": [],
                                    "synsets": [],
                                    "pos": data_items[2]
                                }
                            lemmas[prepared_word]['synsets'].append(new_offset)
                            lemmas[prepared_word]['symbols'] = list(set(lemmas[prepared_word]['symbols'] + symbols))
                            words.append(prepared_word)
                            
                t2 = datetime.datetime.now()
                print("WORDS", t2-t1)
                new_data_items = [new_offset]+data_items[1:3]+[str(len(words)).zfill(2)]
                for word in words:
                    new_data_items.append(word)
                    new_data_items.append("0")
                new_data_items += data_items[idx:]
                # print(new_data_items)
                # print(" ".join(new_data_items))
                new_data_line = "{0} | {1}".format(" ".join(new_data_items), unescape(pt_gloss))
                print("{2} | {0} <=> {1}\n".format(data_items[0],new_offset, file_))
                destination_file.write(new_data_line+"\n")
                insert_mapping(data_items[0],new_offset, file_)
            t_2 = datetime.datetime.now()
            print("LINE", t_2-t_1)
            # new_data_line = " ".join(data_items[:3])

            # print(offset, lemma, pt_gloss)
            # PARTE 1 " ".join(data_items[:3]) + word_count
            # PARTE 2 senses
            # PARTE 3 " ".join(data_items[idx:])
            # |
            # pt_gloss
    destination_file.close()
    indx_file = open("./wordnet/index.{0}".format(file_),'w', encoding="utf-8")
    exec_file = open('./wordnet/{0}.exc'.format(file_), 'w', encoding="utf-8")
    for lemma in lemmas:
        item = lemmas[lemma]
        # 0lemma  1pos  2synset_cnt  3p_cnt  4[ptr_symbol...]  5sense_cnt  6tagsense_cnt   7synset_offset  [synset_offset...] 
        insert_line = "{0} {1} {2} {3} {4} {5} 0 {6}".format(lemma, item['pos'],len(item['synsets']),len(item['symbols']), " ".join(item['symbols']),len(item['synsets']), " ".join(item['synsets']))
        indx_file.write(insert_line+"\n")
        forms = fl.forms(lemma, str(item['pos']).upper())
        for form in forms:
            exec_file.write(form+" "+lemma+"\n")
    indx_file.close()
    exec_file.close()


