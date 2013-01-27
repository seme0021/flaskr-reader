__author__ = 'msemeniuk'
import redis
from scipy import stats
from lexicon import *
from reader2 import *
from score_story import *
import re
import numpy as np
from numpy.random import RandomState
from scipy import stats
from collections import defaultdict


rd = redis.StrictRedis(host="localhost",port=6379, db=1)

def get_capital_words(str):
    return re.findall(r'(?<!\.\s)\b[A-Z][a-z]*\b', str)

def content_strip(str):
    str = str.replace("\xe2\x80\x94","").replace(",","").replace("\"","").replace(":","").replace('"','').replace(")","").replace("(","")
    return str

def get_pop_terms(p):
    words = p.split(" ")
    terms = list()
    skip=False
    for i in range(0,len(words)-1):
        if words[i][:1].isupper() and skip==False:
            #check if this is a multi-word term
            if i != len(words):
                if words[i+1][:1].isupper():
                    word = words[i] + " " + words[i+1]
                    terms.append(word)
                    skip=True
                elif i+1 < len(words):
                    word = words[i]
                    terms.append(word)
            elif i>=len(words):
                word = words[i]
                terms.append(word)
        elif skip:
            skip=False
    return terms

def get_pop_hd_terms(p):
    words = p.split(" ")
    terms = list()
    skip=False
    for i in range(0,len(words)):
        if words[i][:1].isupper() and skip==False:
            #check if this is a multi-word term
            if i != len(words):
                word = words[i].split("'")[0]
                terms.append(word)
            elif i>=len(words):
                word = words[i].split("'")[0]
                terms.append(word)
        elif skip:
            skip=False
    return terms

def find_similar(sid,type):
    try:
        #Get key-terms from headline and first paragraph
        hd = rd.hget("item:%s:%s" % (type,sid),'headline')
        hd = content_strip(hd)
        p1 = rd.get("content:%s:paragraph_1" % sid)
        p1 = content_strip(p1)
        #check if all words are caps
        n_caps = len(get_capital_words(hd))
        n_words = len(hd.split(" "))
        hd_pop = get_pop_hd_terms(hd)
        p1_pop = get_pop_hd_terms(p1)
        d=defaultdict(int)
        terms = hd_pop + p1_pop
        for word in terms:
            d[str(word)] += 1
        #compute score for first 3 paragraphs
        scores = process_story(sid)
        score=np.log(np.average(scores['score'][:3]))
        #Build array for current story
        a = list()
        for item,cnt in d.items():
            a.append(int(cnt))
        a.append(score)
        #itterate over other current stories
        keys = list(set(rd.keys("item:active:*")) - set(["item:active:%s" % sid]))
        pcorr=defaultdict(int)
        for key in keys:
            sidk=int(key.split(":")[2])
            hdk = rd.hget("item:%s:%s" % (type,sidk),'headline')
            hdk = content_strip(hdk)
            p1k = rd.get("content:%s:paragraph_1" % sidk)
            p1k = content_strip(p1k)
            #Check if any of the capital words exist in headline or the paragraph
            n_capsk = len(get_capital_words(hdk))
            n_wordsk = len(hdk.split(" "))
            if n_capsk == n_wordsk:
                hd_popk = get_pop_hd_terms(hdk)
            elif n_capsk != n_wordsk:
                hd_popk = get_pop_terms(hdk)
            p1_popk = get_pop_terms(p1k)
            dk = defaultdict(int)
            termsk = hd_popk + p1_popk
            for word in termsk:
                dk[str(word)] += 1
            scoresk = process_story(sidk)
            scorek=np.log(np.average(scoresk['score'][:3]))
            b=list()
            #check how many terms in a exist in b
            for item,cnt in d.items():
                if dk[str(item)] != 0:
                    pcorr[sidk]+=1
            pcorr[sidk]+=scorek
        pcorrs = sorted(pcorr.iteritems(), key=operator.itemgetter(1),reverse=True)
        return pcorrs
    except AttributeError:
        pass

def build_active_similar(n):
    keys = rd.keys("item:active:*")
    for key in keys:
        sid=int(key.split(":")[2])
        top = find_similar(sid,"news")
        if rd.exists("item:similar:%s" % sid):
            rd.delete("item:similar:%s" % sid)
        try:
            for k,v in top[:5]:
                rd.sadd("item:similar:%s" % sid,k)
        except TypeError:
            pass



