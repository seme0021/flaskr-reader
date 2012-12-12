import redis,re,operator

#redis configuration
REDIS_DB = 1
REDIS_PORT = 6379
REDIS_HOST = 'localhost'
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def get_parameters(sid,pid,n_pid,paragraph):
   parameters = {'sid':[],'pid':[],'nrm_pid':[],'n_words':[],'has_stats':[]}
   n_words = len(re.findall(r'\w+', paragraph))
   nrm_pid = pid/float(n_pid)
   if len(re.findall('[0-9]+', paragraph)) >0:
      has_stats = 1
   else:
      has_stats = 0

   parameters['sid'].append(sid)
   parameters['pid'].append(pid)
   parameters['nrm_pid'].append(nrm_pid)
   parameters['n_words'].append(n_words)
   parameters['has_stats'].append(has_stats)
   
   return parameters

def score(parameters,modelid):
   score = {'sid':[],'pid':[],'score':[]}
   if modelid == 0:
      score_i = -0.39447+ float(parameters['nrm_pid'][0])*float(-0.32789) + float(parameters['n_words'][0])*float(0.40752)+ float(parameters['has_stats'][0])*float(0.08551)
      #rule1: always keep first paragraph
      if parameters['pid'][0] == 1:
         score_i = score_i + 20 
      score['sid'].append(parameters['sid'][0])
      score['pid'].append(parameters['pid'][0])
      score['score'].append(score_i)
      return score
   else:
      print "No Model Selected"


def process_story(sid):
   np = len(r.keys("news:nytimes:%s:paragraph_*" % sid))
   scores = {'sid':[],'pid':[],'score':[]}
   for i in range(1,np):
      paragraph = r.smembers("news:nytimes:%s:paragraph_%s" % (sid,i)).pop()
      p=get_parameters(sid,i,np,paragraph)
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
