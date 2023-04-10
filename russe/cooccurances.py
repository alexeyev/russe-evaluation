# -*- coding: utf-8 -*-

import sys
import csv
csv.field_size_limit(sys.maxsize)
from pymystem3 import Mystem
import time
from collections import OrderedDict
import cProfile
from collections import defaultdict

class CsvHandler:
    #INPUTFILE = 'corpus-ru-dbpedia-short-dea.csv'
    #INPUTFILE = 'wiki-one-line.txt'
    INPUTFILE = 'wiki_noxml_full.txt'
    OUTPUTFILE = 'my_output-large.csv'

    def __init__(self):
        self.file_name = self.INPUTFILE
        self.csvlength = 0
        self.lemmatiser = Mystem()
        #self.freq_dict = {}
        self.fd = defaultdict(dict)

    def do_cprofile(self, func):
        # todo: remove? isn't used anyway
        def profiled_func(*args, **kwargs):
            profile = cProfile.Profile()
            try:
                profile.enable()
                result = func(*args, **kwargs)
                profile.disable()
                return result
            finally:
                profile.print_stats()
        return profiled_func

    def get_freq_dict(self, filename):

        t0 = time.time()
        counter = 0
        with open(filename, 'r') as csvfile:
            datareader = csv.reader(csvfile, delimiter='\t')
            for ln, row in enumerate(datareader):
                if ln % 100 == 0: print(ln, "articles processed")

                input_text = row[2]
                counter += 1
                #if counter > 100:
                    #break
                lemmas = self.get_lem_set(input_text)

                for i, li in enumerate(lemmas):
                    for j, lj in enumerate(lemmas):
                        if i < j:
                            self.fd[li][lj] = 1 if lj not in self.fd[li] else self.fd[li][lj] + 1
                            #key = li + ":::" + lj
                            #if self.freq_dict.get(key, None):
                            #    self.freq_dict[key] += 1
                            #else:
                            #    self.freq_dict[key] = 1
        t1 = time.time()
        for a in self.fd:
            for b in self.fd[a]:
                print(a, b, self.fd[a][b])
        print("Finished. Get input file processing time %2.2f secs, whoosh !" % (t1 - t0))

    #@do_cprofile
    #def sort_dict(self):
    #    return OrderedDict(sorted(self.freq_dict.items(), key=lambda t: t[1], reverse=True))


    def get_lem_set(self, text):

        return_set = set()
        for el in self.lemmatiser.analyze(text):
            analysis = el.get('analysis', None)

            if analysis:
                POS = ['A=', 'S,', 'V=']
                if (analysis[0].get('gr')[0:2] in POS) and (len(analysis[0].get('lex'))>1):
                    return_set.add(analysis[0].get('lex'))

        '''
        for el in self.lemmatiser.lemmatize(text):
            el = el.strip()
            if (el not in punctuation) and (not el.isdigit()):
                return_set.add(el)
        '''

        return return_set

    def output_dict(self, filename, output_dictionary, threshold):
        t0 = time.time()
        with open(filename, 'w', newline='', encoding="UTF-8") as csv_file:

            csv_writer = csv.writer(csv_file, dialect='excel')

            csv_writer.writerow(["First word", "Second word", "Frequency"])

            for key in output_dictionary.keys():

                if output_dictionary[key] > threshold:
                    words = key.split(':::')
                    first_word = words[0]
                    second_word = words[1]

                    csv_writer.writerow([
                        first_word,
                        second_word,
                        output_dictionary[key]
                    ])

            csv_file.flush()
            csv_file.close()
        t1 = time.time()
        print("Finished. Get output file processing time %2.2f secs, whoosh !" % (t1 - t0))


    def process(self):
        self.get_freq_dict(self.file_name)
        #if self.freq_dict:
            #t0 = time.time()
            #sorted_dict = self.sort_dict()
            #t1 = time.time()
            #print("Finished. Sorting -  processing time %2.2f secs, whoosh !" % (t1 - t0))
            #self.output_dict(self.OUTPUTFILE, sorted_dict, 2)
            #self.output_dict(self.OUTPUTFILE, self.freq_dict, 2)


if __name__ == '__main__':
    c = CsvHandler()
    t0 = time.time()
    c.process()
    t1 = time.time()
    print("Finished. Total processing time %2.2f secs, whoosh !" % (t1 - t0))


