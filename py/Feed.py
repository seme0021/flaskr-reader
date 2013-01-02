import urllib2, simplejson

#url = "https://api.twitter.com/1/statuses/user_timeline.json?screen_name=nytimes&count=10"

def feed(sn,n):
   r = urllib2.urlopen("https://api.twitter.com/1/statuses/user_timeline.json?screen_name=" + str(sn) + "&count=" + str(n))
   content = r.read()
   json = simplejson.loads(content)

   items = {'sn':[], 'id':[],'title':[],'url':[]}
   for tweet in json:
      items['sn'].append(sn)
      items['id'].append (tweet['id'])
      end = tweet['text'].find('http')
      items['title'].append(tweet['text'][0:end-1])
      t = tweet['text'][end+5:].find(' ')
      if t > 0:
         items['url'].append(tweet['text'][end:t-1])
      else:
         items['url'].append(tweet['text'][end:])
   return items

