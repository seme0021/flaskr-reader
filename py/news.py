import lxml.html,cookielib,urllib2
#url='http://t.co/gA1jnzsf'

def getny_dtl(tree,s_getny_dtl,ps):
    pid = 0
    for item in ps:
        #print "1. processing " + item
        np = len(tree.xpath(item))
        for p in range(1,np+1):
            pid += 1
            paragraph = []
            pt = tree.xpath(item + '[%s]/text()' % p)
            #print "2. " + ''.join(pt)
            ptl = len(pt)
            if ptl == 1:
                paragraph.append(pt[0])
                #print "3. " +  pt[0]
            elif ptl>1:
                #print "4. N terms: " + str(ptl)
                for i in range(0,ptl):
                    try:
                    #print "4. " +  pt[i] + tree.xpath(item + '[%s]/a[%s]/text()' % (p,i+1))[0]
                        paragraph.append(pt[i] + tree.xpath(item + '[%s]/a[%s]/text()' % (p,i+1))[0])
                    except:
                        #print "5. " + pt[i]
                        paragraph.append(pt[i])
            s_getny_dtl['paragraph'].append(''.join(paragraph))
            s_getny_dtl['id'].append(pid)

def load_page(url):
#Set Cookies and read nytimes
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    request = urllib2.Request(url)
    response = opener.open(request)

    tree = lxml.html.parse(response)
    return tree

def getny(url):
   tree = load_page(url)
   hd = tree.xpath('//div[@id="article"]/div[1]/h1[1]/nyt_headline/text()').pop()
   pg = '//div[@class="articleBody"]/p'
   p1 = '//div[@class="articleBody"]/nyt_text/p'
   outurl = tree.xpath('/html/@itemid')[0]
   tp = tree.xpath('/html/@itemtype')
   get_ny_stories={'id':[],'headline':[],'type':[], 'inurl':[],'outurl':[],'paragraph':[]}

   if tp[0] == "http://schema.org/NewsArticle":
      #print "Parsing Story " + url
      #Grab everyting that belongs to the nyt_text header
      ps=[]
      ps.append(p1)
      ps.append(pg)
      getny_dtl(tree,get_ny_stories,ps)
      get_ny_stories['headline'].append(hd)
      #Get number of pages
      pageNumbers = len(tree.xpath("//ul[@id='pageNumbers']/li[2]/a"))
      for page in range(1,pageNumbers):
          try:
              outurl_id = outurl[0] + "?pagewanted=" + str(page+1) + "&_r=0"
              tree = load_page(outurl_id)
              getny_dtl(tree,get_ny_stories)
          except:
              print "Go to new page failed"

      get_ny_stories['inurl'].append(url)
      get_ny_stories['outurl'].append(outurl)
      get_ny_stories['type'].append(tp)
      return get_ny_stories

#load cnn page
def load_cnn(url):
    tree = load_page(url)
    h_xpath='//h1/text()'
    pg_xpath='//*[@id="cnnContentContainer"]/div[4]/p'
    headline = tree.xpath(h_xpath).pop()
    paragraphs = tree.xpath(pg_xpath)
    type=tree.xpath('/html/@itemtype')[0]
    outurl=tree.xpath('/html/head/meta[22]/@content')[0]
    i=0
    stories={'id':[],'headline':[],'type':[], 'inurl':[],'outurl':[],'paragraph':[]}
    for p in paragraphs:
        try:
            paragraph = p.xpath('text()')[0]
            stories['id'].append(i)
            stories['headline'].append(headline)
            stories['type'].append(type)
            stories['inurl'].append(url)
            stories['outurl'].append(outurl)
            stories['paragraph'].append(paragraph)
            i += 1
        except:
            print "no text found"
    return stories