from nltk.corpus import wordnet as wn 

ss = wn.of2ss("00001377-r")

print(ss, ss.definition())
print(ss.lemmas())
for example in ss.examples():
    print(example)