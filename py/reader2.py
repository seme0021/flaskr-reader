#!/usr/bin/python
from Feed import *
from news import *
import lxml.html, simplejson,urllib2,redis

rd = redis.StrictRedis(host="localhost",port=6379, db=1)



def get_max_sid():
    #1.1: Get sid
    l=rd.smembers("item:sids")
    list = []
    for item in l:
        list.append(int(item))
    list.sort()
    sid=list[-1:][0]+1
    return sid

def add_stories2redis(s,type,sid,act):
    #1.2: Add to known sids
    print "Adding Story to Redis Permanent DB"
    rd.sadd("item:sids", sid)

    #1.3: Add to active sids
    rd.set("item:active:%s" % sid, sid)
    rd.expire("item:active:%s" % sid, 86400)

    #1.4: Story Metadata
    rd.hmset("item:%s:%s" % (type,sid),{"sid":sid,'type':type,'source':act,'inurl':s['inurl'][0],'outurl':s['outurl'][0],'headline':s['headline'][0]})

    #1.5: Add to source sids
    rd.sadd("item:%s:%s:sids" % (type,act),sid)

    #1.6: Add to list of URLs
    print "Adding to list of URLs: " + str(s['outurl'][0])
    rd.sadd("item:urls",s['outurl'][0])

    #2.1: Add paragraph
    j=1
    for pgf in s['paragraph']:
        rd.set("content:%s:paragraph_%s" % (sid, j), ''.join(pgf).replace('\n',''))
        j+=1


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
    for i in range(0,len(words)-1):
        if words[i][:1].isupper() and skip==False:
            #check if this is a multi-word term
            if i != len(words):
                word = words[i]
                terms.append(word)
            elif i>=len(words):
                word = words[i]
                terms.append(word)
        elif skip:
            skip=False
    return terms


def update_pop():
    if rd.exists("active:pop:schema")==0:
        rd.set("active:pop:schema",0)
    schema = int(rd.get("active:pop:schema")) + 1
    keys = rd.keys("item:active*")
    w_ignore = "Then Not A By The More While Even After At To On She Some One Monday Tuesday Thursday Wednesday Thursday Friday Saturday Sunday As I When His Mr Mrs Ms In New It But N This Dr There That They And If He For"
    for key in keys:
        sid = int(key.split(":")[2])
        pkeys = rd.keys("content:%s:paragraph_*" % sid)
        #Process Headline Pop Terms
        headline = rd.hget("item:news:%s" % sid,'headline')
        hp = get_pop_hd_terms(headline.replace("'",""))
        for i in hp:
            if i not in w_ignore:
                if rd.exists("active:pop:%s:%s" % (schema,i)) == 0:
                    rd.hmset("active:pop:%s:%s" % (schema,i), {"term":i,"cnt":1,"sids":str(sid)})
                elif rd.exists("active:pop:%s:%s" % (schema,i)) == 1:
                    cnt=int(rd.hget("active:pop:%s:%s" % (schema,i),"cnt"))+1
                    sids = rd.hget("active:pop:%s:%s" % (schema,i),"sids")
                    if str(sid) not in sids:
                        sids += "," + str(sid)
                    rd.hset("active:pop:%s:%s" % (schema,i),"cnt",int(cnt))
                    rd.hset("active:pop:%s:%s" % (schema,i),"sids",str(sids))

        for pk in pkeys:
            p = rd.get(pk).decode('utf-8')
            for i in get_pop_terms(p):
                if i not in w_ignore:
                    if rd.exists("active:pop:%s:%s" % (schema,i)) == 0:
                        rd.hmset("active:pop:%s:%s" % (schema,i), {"term":i,"cnt":1,"sids":str(sid)})
                    elif rd.exists("active:pop:%s:%s" % (schema,i)) == 1:
                        cnt=int(rd.hget("active:pop:%s:%s" % (schema,i),"cnt"))+1
                        sids = rd.hget("active:pop:%s:%s" % (schema,i),"sids")
                        if str(sid) not in sids:
                            sids += "," + str(sid)
                        rd.hset("active:pop:%s:%s" % (schema,i),"cnt",int(cnt))
                        rd.hset("active:pop:%s:%s" % (schema,i),"sids",str(sids))
    rd.set("active:pop:schema",schema)
    #Clean-Up Keys Where count=1
    keys = rd.keys("active:pop:%s" % schema)
    for key in keys:
        try:
            cnt = rd.hget(key,'cnt')
            if cnt == 1:
                rd.delete(key)
        except:
            pass

def reader(twitter,n):
    for act in twitter:
        print "Reading Twitter Feed From: " + act
        stories=feed(act,n)
        print stories
        for story in stories['url']:
            sid=get_max_sid()

            #Process nytimes stories
            if act=="nytimes":
                try:
                    print "Reading NYTimes Story " + story + " with sid: " + str(sid)
                    s = getny(story)
                    print "Story Type: " + s['type'][0][0]
                    if s['type'][0][0] == "http://schema.org/NewsArticle" and rd.sismember("item:urls",s['outurl'][0]) == False:
                        print "Adding story id to current feed"
                        add_stories2redis(s,"news",sid,act)
                    elif rd.sismember("item:urls",s['outurl'][0]) == True:
                        print "Story already exists"
                except:
                    print "Story Failed"

            #Process cnn stories
            elif act=="cnn":
                try:
                    print "Reading CNN Story " + story + " with sid: " + str(sid)
                    s=load_cnn(story)
                    if s['type'][0] == "http://schema.org/NewsArticle" and rd.sismember("item:urls",s['outurl'][0]) == False:
                        print "Addint story id to current feed"
                        add_stories2redis(s,"news",sid,act)

                except:
                    print "Story Failed"

            #Process HuffPost Stories
            elif act=="HuffingtonPost":
                try:
                    print "Reading Huffington Post Story " + story + " with sid: " + str(sid)
                    s = get_huff(story)
                    if s['type'][0] == "http://schema.org/Article" and rd.sismember("item:urls",s['outurl'][0]) == False:
                        print "Adding story id to current feed"
                        add_stories2redis(s,"news",sid,act)
                except:
                    print "Story Failed"

            elif act=="Reuters":
                try:
                    print "Reading Reuters Story " + story + " with sid: " + str(sid)
                    s=get_reuters(story)
                    if s['type'][0] == "News" and rd.sismember("item:urls", s['outurl'][0]) == False:
                        print "adding story id to current feed"
                        add_stories2redis(s,"news",sid,act)
                except:
                    print "Story Failed"
    update_pop()



def convert_item_sids():
    old = map(int,list(rd.smembers("news:nytimes:sid")))
    for sid in old:
        rd.sadd("item:sids", sid)

def convert_active_sids():
    old=rd.keys("*active*")
    for key in old:
        sid = int(key.split(":")[2])
        rd.set("item:active:%s" % sid, sid)
        rd.expire("item:active:%s" % sid, 86400)

def build_metadata():
    sids = map(int,list(rd.smembers("item:sids")))
    for sid in sids:
        id = rd.keys("*:%s:headline" % sid)[0]
        type = id.split(":")[0]
        source = id.split(":")[1]
        headline = rd.smembers(id).pop().replace("[","").replace("]","")
        outurl = rd.smembers("news:nytimes:%s:url" % sid).pop().replace("[","").replace("]","").replace("'","")
        inurl = rd.smembers("news:nytimes:%s:inurl" % sid).pop().replace("[","").replace("]","").replace("'","")
        rd.hmset("item:%s:%s" % (type,sid),{"sid":sid,'type':type,'source':source,'inurl':inurl,'outurl':outurl,'headline':headline})

def item_urls():
    keys = list(rd.smembers("news:nytimes:inurl"))
    for key in keys:
        rd.sadd("item:urls",key)

def build_act_type_keys():
    sids = map(int,list(rd.smembers("item:sids")))

def convert_paragraphs():
    sids = map(int,list(rd.smembers("item:sids")))
    for sid in sids:
        paragraphs = rd.keys("news:*:%s:paragraph_*" % sid)
        for p in paragraphs:
            print p
            pid = p.split("_")[1]
            content=rd.smembers(p).pop()
            rd.set("content:%s:paragraph_%s" % (sid,pid), content)

if __name__ == '__main__':
    twitter=['nytimes','cnn','HuffingtonPost']
    reader(twitter,10)
