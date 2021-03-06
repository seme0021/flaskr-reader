import redis,re,operator, numpy as nm,csv, os
from collections import defaultdict
from lexicon import *

#redis configuration
REDIS_DB = 1
REDIS_PORT = 6379
REDIS_HOST = 'localhost'
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def get_parameters(sid,pid,n_pid,c,paragraph,l_time):
   parameters = {'sid':[],'pid':[],'nrm_pid':[],'n_words':[],'has_stats':[], 'pop_score':[],'recency_flg':[],'quote_flg':[],'quote_len':[],'quote_npop_flg':[]}
   n_words = len(re.findall(r'\w+', paragraph))
   nrm_pid = pid/float(n_pid)
   pop_score = get_pop_score(paragraph,c)
   #check if paragraph contains statistics/data
   if len(re.findall('[0-9]+', paragraph)) >0:
      has_stats = 1
   else:
      has_stats = 0

   #Check for quotes, and get length of quote
   quote_flg=0
   quote_len=0
   quote_pop_flg=0
   quote_pop_len=0
   quote_npop_flg=0
   p=paragraph.decode('utf8').replace(u"\u201c","^").replace(u"\u201d","^")
   l=len(p.split('^'))
   if l>1:
       quote_flg=1
       quote_len=nm.log(len(p.split('^')[1]))

   if quote_flg==1 and pop_score==0 and n_words>=25:
       quote_npop_flg=1

   #compute recency indicator
   recency_flg = 0
   for term in l_time:
       if term in paragraph.lower():
           recency_flg = 1

   #Append parameters
   parameters['sid'].append(sid)
   parameters['pid'].append(pid)
   parameters['nrm_pid'].append(nrm_pid)
   parameters['n_words'].append(n_words)
   parameters['has_stats'].append(has_stats)
   parameters['pop_score'].append(pop_score)
   parameters['recency_flg'].append(recency_flg)
   parameters['quote_flg'].append(quote_flg)
   parameters['quote_len'].append(quote_len)
   parameters['quote_npop_flg'].append(quote_npop_flg)
   
   return parameters

#Function: Get words with capital letter
def get_capital_words(str):
    return re.findall(r'(?<!\.\s)\b[A-Z][a-z]*\b', str)

#Function: Gets most common, takes list [key,count] as input
def most_common(d,n):
    list = sorted(d, key=lambda d: -d[1])[:n]
    return list


#Function: Get most frequent capital words
def most_freq(sid):
    np = len(r.keys("news:nytimes:%s:paragraph_*" % sid))
    w_ignore = "The At Monday Tuesday Thursday Wednesday Thursday Friday Saturday Sunday Mr Mrs Ms In"
    w_caps = list()
    for i in range(1,np):
        paragraph = r.smembers("news:nytimes:%s:paragraph_%s" % (sid,i)).pop()
        caps = get_capital_words(paragraph)
        for word in caps:
            if word not in w_ignore:
               w_caps.append(word)
    w_freqs = defaultdict(int)
    for word in w_caps:
       w_freqs[word] += 1
    d=w_freqs.items()
    c={}
    for word, count in most_common(d,4):
        if count>1:
           c[word] =  int(count)
    return c

#Function: Check if paragraph contains words of interest
def get_pop_score(paragraph,c):
    v=1
    for key,value in c.iteritems():
        if key in paragraph:
            v += value
    o_v = nm.log(v)
    return o_v

def score(parameters,modelid):
    #                                Estimate  Std. Error t value Pr(>|t|)
    #(Intercept)                     -0.06168    0.18046  -0.342   0.7329
    #as.numeric(df$nrm_pid)          -0.38270    0.08966  -4.268 2.97e-05 ***
    #log(as.numeric(df$n_words) + 1)  0.29227    0.04984   5.864 1.70e-08 ***
    #as.numeric(df$has_stats)         0.11143    0.05961   1.869   0.0629 .
    #as.numeric(df$pop_score)         0.06439    0.02510   2.565   0.0110 *
    #as.numeric(df$quote_npop_flg)    0.20685    0.10542   1.962   0.0511 .

   score = {'sid':[],'pid':[],'score':[]}
   if modelid == 0:
      score_i = -0.06168 + float(parameters['nrm_pid'][0])*float(-0.38270) + float(parameters['n_words'][0])*float(0.29227)+ float(parameters['has_stats'][0])*float(0.11143) + float(parameters['pop_score'][0])*float(0.06439) + float(parameters['quote_npop_flg'][0])*float(0.20685)
      #rule1: always keep first paragraph
      if parameters['pid'][0] == 1:
         score_i += 20
      score['sid'].append(parameters['sid'][0])
      score['pid'].append(parameters['pid'][0])
      score['score'].append(score_i)
      return score
   else:
      print "No Model Selected"

uread = r.keys("user:*:read:sids")
ukeys = {}
for u in uread:
    user = int(u.split(":")[1])
    ukeys[user]=r.smembers(u)

#Function: Build research data-set
def build_rnd_dsn(path,file,l_time):
   keys=r.keys("nytimes:usps:*:*:*")
   os.chdir(path)
   with open(file, "wb") as csvfile:
       pw = csv.writer(csvfile, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL)
       pw.writerow(['hash'] + ['uid'] + ['sid'] + ['pid'] + ['nrm_pid'] + ['n_words'] + ['has_stats'] + ['pop_score'] + ['recency_flg'] + ['quote_flg'] + ['quote_len'] + ['quote_npop_flg'] + ['y_score'])
   #Itterate over read keys
   for key in keys:
      user=int(key.split(":")[2])
      sid=int(key.split(":")[3])
      pid=int(key.split(":")[4])
      hash = str(user) + str(sid) + str(pid)
      n_pid = len(r.keys("nytimes:usps:%s:%s:*" % (user,sid)))
      #compute c: most frequent (c)apitalized terms
      c = most_freq(sid)
      paragraph = r.smembers("news:nytimes:%s:paragraph_%s" % (sid,pid)).pop()
      p=get_parameters(sid,pid,n_pid,c,paragraph,l_time)
      s=r.smembers("nytimes:usps:%s:%s:%s" % (user,sid,pid))
      #Write row to csv
      pw = open(file, "a")
      row = str(hash) + "," + str(user) + "," + str(sid) + "," + str(pid) + "," + str(p['nrm_pid'][0]) + "," + str(p['n_words'][0]) + "," + str(p['has_stats'][0]) + "," + str(p['pop_score'][0]) + "," + str(p['recency_flg'][0]) + "," + str(p['quote_flg'][0]) + "," + str(p['quote_len'][0]) + "," + str(p['quote_npop_flg'][0])  + "," + s.pop() + "\n"
      pw.write(row)

def process_story(sid):
   np = len(r.keys("news:nytimes:%s:paragraph_*" % sid))
   c = most_freq(sid)
   l_time=time()
   scores = {'sid':[],'pid':[],'score':[]}
   for i in range(1,np):
      paragraph = r.smembers("news:nytimes:%s:paragraph_%s" % (sid,i)).pop()
      p=get_parameters(sid,i,np,c,paragraph,l_time)
      s=score(p,0)
      scores['sid'].append(s['sid'][0])
      scores['pid'].append(s['pid'][0])
      scores['score'].append(s['score'][0])
   return scores

def top5(scores):
   d={}
   for p in range(0,len(scores['pid'])-1):
      d[scores['pid'][p]] = scores['score'][p]
   ds = sorted(d.iteritems(), key=operator.itemgetter(1),reverse=True)
   top5 = ds[:5]
   top5.sort()
   return top5 
