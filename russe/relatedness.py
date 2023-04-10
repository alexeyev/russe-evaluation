# -*- coding: utf-8 -*-

# Read data from xml files
import codecs
from lxml import etree as ElementTree
from collections import defaultdict
import traceback
from pandas import read_csv
from os.path import join
from russe.common import get_pos
from pandas import DataFrame

# from nlp.morpho.mystem import analyze_simple
from russe.dsl_nlp_utils import analyze_simple

# imports from dsl nlp library
# todo: can't find this library in 2023
# from nlp.patterns import re_numbers, re_latin_chars
from russe.dsl_nlp_utils import re_numbers, re_latin_chars

from russe.dsl_nlp_utils import prt
# from nlp.common import prt


T = {u"выше": u"hyper",
     u"ниже": u"hypo",
     u"часть": u"mero",
     u"целое": u"holon",
     u"асц": u"assoc",
     u"асц1": u"assoc1",
     u"асц2": u"assoc2"}

MAX_REL_NUM = 30
WHITE_LIST = "white-list.csv"
BLACK_LIST = "black-list.csv"
MAX_PAIRS_NUM = 999999999


def load_syn(syn_fpath):
    with codecs.open(syn_fpath, 'rt') as syn_file:
        syn_tree = ElementTree.parse(syn_file)

    syn = defaultdict(set)
    for i, node in enumerate(syn_tree.iter()):
        if node.tag == "entry_rel" and "entry_id" in node.attrib and "concept_id" in node.attrib:
            syn[node.attrib["concept_id"]].add(node.attrib["entry_id"])
            
    print(i, "synonyms loaded")
    print(len(syn), "concepts loaded")

    return syn


def load_entries(fpath):
    with codecs.open(fpath, 'rt') as f:
        tree = ElementTree.parse(f)

    entries = defaultdict(set)
    for i, node in enumerate(tree.iter()):
        try:
            if node.tag != "entry": continue

            lemma = [cnode.text for cnode in node if cnode.tag == "lemma"][0].lower()
            if " " in lemma or re_numbers.search(lemma) or re_latin_chars.search(lemma):
                continue  # print ">>>", lemma
            else:
                entries[node.attrib["id"]] = lemma
        except:
            print("warning: line", i)
            #print traceback.format_exc()
            
    print(len(entries), "text entries loaded")
    print(i, "text entries total")
    return entries


def generate_synsets(syn, entries, concepts, selected_words, add_concepts=False, only_selected=False):
    synsets = defaultdict(set)
    word_num = 0
    skipped = 0
    matched_num = 0

    for i, s in enumerate(syn):
        
        # add all synonyms to a synset
        ss = set()
        for e in syn[s]:
            if e in entries:
                ss.add(entries[e])
                word_num += 1
        if add_concepts:
            if s in concepts: ss.add(concepts[s])
            else: print("warning: concept not found", s)

        # select synset?
        if only_selected:
            select = False
            for word in ss:
                if word in selected_words:
                    select = True
                    matched_num += 1 
                    break
        else:
            select = True
        
        # save synset if selected
        if len(ss) > 1 and select: synsets[s] = ss
        else: skipped += 1
                
    print(matched_num, "words matched")
    print(len(synsets), "synsets")
    print(word_num, "words in synsets")
    print(skipped, "synsets skipped")

    return synsets


def load_voc(voc_fpath):
    df = read_csv(voc_fpath, ',', encoding='utf8')
    voc = {row["word"]: 1 for i, row in df.iterrows()}
    if "" in voc: del voc[""]
    if None in voc: del voc[None]
    if " " in voc: del voc[" "]
        
    return voc


def load_concepts(fpath):
    with codecs.open(fpath, 'rt') as f:
        tree = ElementTree.parse(f)
    
    concepts = {}
    for i, node in enumerate(tree.iter()):
        try:
            if node.tag != "concept": continue
            name = [cnode.text for cnode in node if cnode.tag == "name"][0].lower()
            #if " " in name or re_numbers.search(name) or re_latin_chars.search(name):
            #    continue
            #else:
            concepts[node.attrib["id"]] = name
        except:
            print("warning: line", i)
            print(traceback.format_exc())
            
    print(len(concepts), "concepts loaded")
    return concepts


def load_relations(fpath):
    with codecs.open(fpath, 'rt') as f:
        tree = ElementTree.parse(f)
    
    relations = defaultdict(list)
    for i, node in enumerate(tree.iter()):
        try:
            if node.tag != "rel" or any([a not in node.attrib for a in ["from", "to", "name"]]):
                continue
            relations[node.attrib["from"]].append( (node.attrib["to"], node.attrib["name"].lower()) )
        except:
            print("warning: line", i)
            print(traceback.format_exc())
            
    print(len(relations), "relations loaded")
    return relations


def generate_relations(relations, entries, synsets, output_fpath, symmetric=False):
    
    with codecs.open(output_fpath, "w", "utf-8") as output_file:
        num = 0
        skipped_num = 0
        print("word1,word2,sim", file=output_file)

        for src in relations:
            for dst, sim in relations[src]:
                # generate pairwise relations beteween synsets
                for i, wi in enumerate(synsets[src]):
                    for j, wj in enumerate(synsets[dst]):
                        if i > j: # do not generate symmetric, they are alredy in
                            print("%s,%s,%s" % (wi, wj, T[sim]), file=output_file)
                            num += 1

        print("#relations b/w words:", num)
        print("#skipped relations b/w concepts:", skipped_num)
        print("concept relations:", output_fpath)

        
def generate_cohypo(relations, entries, synsets, concepts, output_fpath):
    
    with codecs.open(output_fpath, "w", "utf-8") as output_file:
        num = 0
        numc = 0
        skipped_num = 0
        print >> output_file, "word1,word2,sim"
        for k, src in enumerate(relations):
            for dst_i, sim_i in relations[src]:
                for dst_j, sim_j in relations[src]:
                    cohyponyms = (dst_i != dst_j and
                                  dst_i in concepts and
                                  dst_j in concepts and
                                  T[sim_i] == "hypo" and
                                  T[sim_j] == "hypo")
                    if not cohyponyms: continue
                    numc += 1
                    
                    # generate pairwise relations beteween cohyponym synsets
                    for wi in synsets[dst_i]:
                        for wj in synsets[dst_j]:
                            if wi != wj: # do generate symmetric
                                print >> output_file, "%s,%s,cohypo" % (wi, wj) #, concepts[src].replace(","," "))
                                num += 1
                     
        print("#cohypo:", num, numc)
        print("cohypo relations:", output_fpath)
         
    
def mix_filter_relations(output_syn_fpath, output_rel_fpath, output_cohypo_fpath, output_fpath, selected_words, cohypo=False):
    syn_df = read_csv(output_syn_fpath, ',', encoding='utf8')
    rel_df = read_csv(output_rel_fpath, ',', encoding='utf8')
    print("relations loaded")
    df = syn_df.append(rel_df)
    if cohypo:
        cohypo_df = read_csv(output_cohypo_fpath, ',', encoding='utf8')
        df = df.append(cohypo_df)
    
    # for i, row in df.iterrows():
    #     if i % 100000 == 0: print i
    #     if row["word1"] in ["болезнь", u"болезнь"]:
    #         a = get_pos(row["word1"])[0] != "S" or get_pos(row["word2"])[0] != "S"
    #         b = row["sim"] not in ["hyper", "hypo", "syn"]
    #         print row["word1"], row["word2"], row["sim"], a, b

    # return 

    df = df.sort(['word1', 'sim'], ascending=[1, 1])
    print("sorted")
    df.to_csv(output_fpath + ".all", sep=',', encoding='utf-8', index=False)
    print("relations all:", output_fpath + "-all.csv")

    # Filter according to relation types
    rels2drop = [i for i, row in df.iterrows() if row["sim"] not in ["hyper", "hypo", "syn"]]
    df = df.drop(rels2drop)
    df.to_csv(output_fpath + ".hhs" , sep=',', encoding='utf-8', index=False)
    print("#relations hypo/hyper/syn:", len(df))
    print("relations hypo/hyper/syn:", output_fpath + ".hhs")

    # Filter accoring to part of speech
    #rels2drop = [i for i, row in df.iterrows() if get_pos(row["word1"])[0] != "S" or get_pos(row["word2"])[0] != "S"]
    r2d = []
    with codecs.open("pos", "w", "utf-8") as pos_file:
        for i, row in df.iterrows():
            pos1 = get_pos(row["word1"])[0]
            pos2 = get_pos(row["word2"])[0]
            drop = pos1 != "S" or pos2 != "S"
            if drop:
                r2d.append(i)
            print("%s,%s,%s,%s,%s" % (row["word1"], row["word2"], row["sim"], pos1, pos2), file=pos_file)

    df = df.drop(r2d)
    df.to_csv(output_fpath + ".pos" , sep=',', encoding='utf-8', index=False)
    print("#relations pos:", len(df))
    print("relations pos:", output_fpath + ".pos")
    
    # Filter according to vocabulary
    rels2drop = [i for i, row in df.iterrows() if row["word1"] not in selected_words]
    print("#relations to drop:", len(rels2drop))
    df = df.drop(rels2drop)
    df = df.drop_duplicates()
    print("#final relations", len(df))
    df.to_csv(output_fpath , sep=',', encoding='utf-8', index=False)
    print("relations:", output_fpath)


def generate_best(input_fpath, best_fpath, res_fpath):
    wdf = read_csv(join(res_fpath, WHITE_LIST), ',', encoding='utf8')
    white = {row["word"]: 1 for i, row in wdf.iterrows()}
    bdf = read_csv(join(res_fpath,BLACK_LIST), ',', encoding='utf8')
    black = {row["word"]: 1 for i, row in bdf.iterrows()}

    df = read_csv(input_fpath, ',', encoding='utf8')
    gdf = df.groupby(["word1"], sort=False).count()
    words2drop = {row.name: row["word2"] for i, row in gdf.iterrows()
        if row.name in black or (row["word2"] > MAX_REL_NUM and row.name not in white)}
    indexes2drop = [i for i, row in df.iterrows() if row["word1"] in words2drop or row["word1"] == row["word2"]]
    df = df.drop(indexes2drop)
    print("#words2drop:", len(words2drop))
    print("#relations2drop:", len(indexes2drop))
    print("#best relations:", len(df))
    
    df.to_csv(best_fpath, sep=',', encoding='utf-8', index=False)
    print("best relations:", best_fpath)



def clean_ae_fuzzy_duplicates(input_fpath, output_fpath):
    build_row = lambda x: {"sim": x["sim"], "dir": x["dir"], "inv": x["inv"]}
    build_full_row = lambda x: {"word1": x["word1"], "word2": x["word2"], 
                                "sim": x["sim"], "dir": x["dir"], "inv": x["inv"]}
    
    df = read_csv(input_fpath, ',', encoding='utf8')

    # lemmatize
    r = defaultdict(dict)

    for i, row in df.iterrows():
        word1, _ = analyze_simple(row["word1"])[0]
        word2, _ = analyze_simple(row["word2"])[0]
        
        if word1 in r and word2 in r[word1]:
            # Pair is not new -- check it 
            new_val = row["dir"] + row["inv"]
            old_val = r[word1][word2]["dir"] + r[word1][word2]["inv"]
            if new_val > old_val:
                # Use new pair
                r[word1][word2] = build_full_row(row)
                print(".", end=" ")
            else:
                # Keed old pair
                pass 
        else:
            # Pair is new -- add it
            r[word1][word2] = build_full_row(row)
        
        if i > MAX_PAIRS_NUM: break
    print("")
    
    # convert to the right format
    rr = [{"word1":r[w1][w2]["word1"], "word2":r[w1][w2]["word2"],
           "sim":r[w1][w2]["sim"], "dir":r[w1][w2]["dir"], "inv":r[w1][w2]["inv"] }
          for w1 in r for w2 in r[w1]]
    
    
    
    # create a new table with lemmas
    
    df = DataFrame(rr)
    df.to_csv(output_fpath, sep=',', index=False, encoding='utf-8', cols=["word1","word2","sim","dir","inv"])    
    print("output:", output_fpath)
