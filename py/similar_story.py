__author__ = 'msemeniuk'
import redis
from scipy import stats
from lexicon import *
from reader2 import *
from score_story import *
import re
from collections import defaultdict

rd = redis.StrictRedis(host="localhost",port=6379, db=1)

def get_capital_words(str):
    return re.findall(r'(?<!\.\s)\b[A-Z][a-z]*\b', str)

def find_similar(sid,type):
    #Get key-terms from headline and first paragraph
    hd = rd.hget("item:%s:%s" % (type,sid),'headline').decode('utf-8').replace(",","").replace("\"","").replace(":","").replace('"','').replace(")","").replace("(","")
    p1 = rd.get("content:%s:paragraph_1" % sid).decode('utf-8').replace(",","").replace("\"","").replace(":","").replace('"','').replace(")","").replace("(","")
    #check if all words are caps
    n_caps = len(get_capital_words(hd))
    n_words = len(hd.split(" "))
    if n_caps == n_words:
        hd_pop = get_pop_hd_terms(hd)
    elif n_caps != n_words:
        hd_pop = get_pop_terms(hd)
    p1_pop = get_pop_terms(p1)
    d=defaultdict(int)
    terms = hd_pop + p1_pop
    for word in terms:
        d[str(word)] += 1
    key_terms=list()
    for item,cnt in d.items():
        list.append(item)
    #compute score for first
    scores = process_story(sid)
