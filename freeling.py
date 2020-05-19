import sqlite3

class Freeling:
    def __init__(self):
        self.connection = sqlite3.connect("./data/freeling.db")
    
    def forms(self, lemma, pos):
        c = self.connection.cursor()
        pos = pos.upper()
        # c.execute("SELECT distinct(form) FROM word WHERE lemma = '"+lemma+"' and pos like '"+pos+"%' and form <> '"+lemma+"'")
        c.execute("SELECT distinct(form) FROM word WHERE lemma = ? and pos like '"+pos+"%' and form <> ?",(lemma, lemma, ))
        result = []
        for row in c.fetchall():
            result.append(row[0])
        c.close()
        return result

# f = Freeling()

# for form in f.forms("ato",'N'):
#     print(form)