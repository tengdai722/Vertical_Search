import sys
import csv

csv.field_size_limit(sys.maxsize)
import pandas as pd

f = open("articles1.csv", 'rt')
fDict = open("newCorpusIdx.txt", "a")
reader = csv.reader(f)
i = 0
for row in reader:
    if i > 0:
        title = row[2]
        if '-' in title:
            title = title[0:title.rfind('-') - 1]
        idx = int(row[1])
        newFileName = "new_corpus/" + str(idx) + ".txt"
        newFile = open(newFileName, "w+")
        newFile.write(title + "\n")
        newFile.write(row[9])
        newFile.close()
        fDict.write(str(idx) + " " + title + "\n")
    i += 1

#print (article)
