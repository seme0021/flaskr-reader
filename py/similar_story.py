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
    str = str.replace("\xe2\x80\x94","'").replace("\xe2\x80\x99","'").replace(",","").replace("\"","").replace(":","").replace('"','').replace(")","").replace("(","")
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

def tanimoto(sid,type):
    try:
        #Get key-terms from headline and first paragraph
        try:
            hd = content_strip(rd.hget("item:%s:%s" % (type,sid),'headline'))
            p1 = content_strip(rd.get("content:%s:paragraph_1" % sid))
        except AttributeError:
            hd = ""
            p1 = ""
        terms = set(get_pop_hd_terms(hd) + get_pop_hd_terms(p1))
        #Compute score against other active stories
        keys = list(set(rd.keys("item:active:*")) - set(["item:active:%s" % sid]))
        pcorr=defaultdict(int)
        for key in keys:
            sidk=int(key.split(":")[2])
            try:
                hdk = content_strip(rd.hget("item:%s:%s" % (type,sidk),'headline'))
                p1k = content_strip(rd.get("content:%s:paragraph_1" % sidk))
            except AttributeError:
                hdk = ""
                p1k = ""
            termsk = set(get_pop_hd_terms(hdk) + get_pop_hd_terms(p1k))
            c1,c2,shr=0,0,0
            for w in set(list(terms) + list(termsk)):
                if w in terms:
                    c1+=1
                if w in termsk:
                    c2+=1
                if (w in terms) and (w in termsk):
                    shr+=1
            score = 1.0 - (float(shr)/max(1,(c1 + c2 - shr)))
            pcorr[sidk]=score
        pcorrs = sorted(pcorr.iteritems(), key=operator.itemgetter(1),reverse=True)
        return pcorrs
    except AttributeError:
        pass




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
        top = tanimoto(sid,"news")
        if rd.exists("item:similar:%s" % sid):
            rd.delete("item:similar:%s" % sid)
        try:
            for k,v in top[:5]:
                rd.sadd("item:similar:%s" % sid,k)
        except TypeError:
            pass

def pop_author():
    d=defaultdict(int)
    keys = rd.keys("item:news:*")
    for i in range(900,1095):
        key="item:news:%s" % i
        print key
        sid = int(key.split(':')[2])
        if sid > 900:
            try:
                author =  rd.hget(key,'author').upper()
                if len(author) >= 3:
                    d[author] += 1
            except:
                pass
    return d

def author_words():
    d={}
    keys = rd.keys("item:news:*")
    type = "news"
    for key in keys:
        try:
            sid = int(key.split(":")[2])
        except ValueError:
            sid=0
        author=None
        if sid>700:
            author = rd.hget(key,'author')
        if (author) and sid>700:
            try:
                try:
                    hd = get_pop_hd_terms(content_strip(rd.hget("item:%s:%s" % (type,sid),'headline')))
                    pgs = rd.keys("content:%s:paragraph_*" % sid)
                except AttributeError:
                    hd = ""
                    pgs = ""
                words = list()
                for p in pgs:
                    pg = get_pop_hd_terms(content_strip(rd.get(p)))
                    for word in pg:
                        word = content_strip(word).split("'")[0]
                        if (word not in w_ignore) and (len(word)>2):
                            words.append(word)
                terms = words + hd
                wcnt = defaultdict(int)
                for i in terms:
                    wcnt[i]+=1
                wcnt=sorted(wcnt.iteritems(), key=operator.itemgetter(1),reverse=True)[:15]
                d[author] = wcnt
            except AttributeError:
                pass
    return d

def author_words2redis(d):
    for i in d.items():
        author = i[0].strip().replace(".","").replace(" ","-")
        if rd.exists("author:terms:%s" % author):
            rd.delete("author:terms:%s" % author)
        for w,c in i[1]:
            term = str(w) + ":" + str(c)
            rd.sadd('author:terms:%s' % author,term)

def author_schema():
    keys = rd.keys("item:news:*")
    for key in keys:
        try:
            sid = int(key.split(":")[2])
        except ValueError:
            sid=0
        author=None
        if sid>700:
            author = rd.hget(key,'author')
        if (author) and sid>700:
            author=author.strip().replace(" ","-").replace(".","")
            publication = rd.hget(key,'source')
            rd.hmset("author:%s" % author,{'publication':publication})


def author_story():
    keys = rd.keys("item:news:*")
    for key in keys:
        try:
            sid = int(key.split(":")[2])
        except ValueError:
            sid=0
        author=None
        if sid>700:
            author = rd.hget(key,'author')
        if (author) and sid>700:
            author=author.strip().replace(" ","-").replace(".","")
            rd.sadd("author:sids:%s" % author,sid)

def get_latest_tweets(tid):
    r = urllib2.urlopen("https://api.twitter.com/1/statuses/user_timeline.json?screen_name=" + str(tid) + "&count=" + str(10))
    content = r.read()
    json = simplejson.loads(content)
    l=list()
    for tweet in json:
        if not tweet['in_reply_to_status_id']:
            l.append(tweet['id_str'])
    return l[:3]

def updt_twitter_acct(author,acct):
    rd.hset('author:%s' % author,'twitter',acct)

def updt_latest_tweets(author):
    if rd.exists('author:tweets:%s' % author):
        rd.delete('author:tweets:%s' % author)
    handle=rd.hget('author:%s' % author,'twitter')
    print handle
    tweets=get_latest_tweets(handle)
    print tweets
    for t in tweets:
        rd.sadd('author:tweets:%s' % author,t)


