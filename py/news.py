import lxml.html,cookielib,urllib2
from lxml import etree
from collections import defaultdict
#url='http://t.co/gA1jnzsf'


def getny_dtl(tree,s_getny_dtl,ps):
    pid = 0
    for item in ps:
        np = len(tree.xpath(item))
        for p in range(1,np+1):
            pid += 1
            paragraph = []
            pt = tree.xpath(item + '[%s]' % p)[0]
            etree.strip_tags(pt,'a','c')
            paragraph = "".join(pt.xpath("text()"))
            s_getny_dtl['paragraph'].append(paragraph)
            s_getny_dtl['id'].append(pid)

def load_page(url):
#Set Cookies and read nytimes
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    request = urllib2.Request(url)
    response = opener.open(request)

    tree = lxml.html.parse(response)
    return tree

def get_reuters(url,schema):
    tree = load_page(url)
    headline = tree.xpath("//h1")[0].xpath("text()")[0]
    main_p = tree.xpath("//span[@class='focusParagraph']/p/text()")[0]
    pg = tree.xpath("//span[@id='articleText']/p")
    try:
        w = tree.xpath("//p[@class='byline']/text()")[0].replace("By ","").split(" and ")
        #Add author and possibly co-author
        if len(w) == 1:
            schema['author'].append(w[0])
        elif len(w) != 1:
            schema['author'].append(w[0])
            schema['co-author'].append(w[1])
    except IndexError:
        pass
    type = "News"
    outurl = tree.docinfo.URL
    #append first paragraph
    schema['id'].append(1)
    schema['headline'].append(headline)
    schema['type'].append(type)
    schema['inurl'].append(url)
    schema['outurl'].append(outurl)
    schema['paragraph'].append(main_p)
    i=2
    for p in pg:
        try:
            paragraph = p.xpath("text()")[0]
            if (paragraph[0] == '*') or (paragraph[:2] == 'By'):
                if paragraph[:2] == 'By':
                    author = paragraph.split('and')[0].split('By')[1].strip()
                    #author = paragraph.split('and')[1].strip()
                    schema['author'].append(author)
            elif paragraph[0] != '*':
                schema['id'].append(i)
                schema['headline'].append(headline)
                schema['type'].append(type)
                schema['inurl'].append(url)
                schema['outurl'].append(outurl)
                schema['paragraph'].append(paragraph)
                i+=1
        except IndexError:
            pass
        i+=1
    return schema

def get_huff(url,schema):
    tree = load_page(url)
    pg = '//div[@class="articleBody"]/p'
    headline = tree.xpath("//h1[@class='title-news']/text()")[0]
    headline = ' '.join(headline.split())
    type = tree.xpath("//div[@id='news_content']/@itemtype")[0]
    outurl=tree.docinfo.URL
    w=tree.xpath("//a[@rel='author']/text()")[0].split(" and ")
    #Add author and possibly co-author
    if len(w) == 1:
        schema['author'].append(w[0])
    elif len(w) != 1:
        schema['author'].append(w[0])
        schema['co-author'].append(w[1])
    i=0
    for p in tree.xpath(pg):
        etree.strip_tags(p,'a','c')
        paragraph = "".join(p.xpath("text()"))
        i+=1
        schema['id'].append(i)
        schema['headline'].append(headline)
        schema['type'].append(type)
        schema['inurl'].append(url)
        schema['outurl'].append(outurl)
        schema['paragraph'].append(paragraph)
    return schema


def getny(url,schema):
   tree = load_page(url)
   hd = tree.xpath('//div[@id="article"]/div[1]/h1[1]/nyt_headline/text()').pop()
   pg = '//div[@class="articleBody"]/p'
   p1 = '//div[@class="articleBody"]/nyt_text/p'
   outurl = tree.docinfo.URL
   tp = tree.xpath('/html/@itemtype')
   w = tree.xpath("//span[@itemprop='name']/text()")[0].split(" and ")
   #Add author and possibly co-author
   if len(w) == 1:
       schema['author'].append(w[0])
   elif len(w) != 1:
       schema['author'].append(w[0])
       schema['co-author'].append(w[1])

   if tp[0] == "http://schema.org/NewsArticle":
      #print "Parsing Story " + url
      #Grab everyting that belongs to the nyt_text header
      ps=[]
      ps.append(p1)
      ps.append(pg)
      getny_dtl(tree,schema,ps)
      schema['headline'].append(hd)
      #Get number of pages
      pageNumbers = len(tree.xpath("//ul[@id='pageNumbers']/li[2]/a"))
      for page in range(1,pageNumbers):
          try:
              outurl_id = outurl[0] + "?pagewanted=" + str(page+1) + "&_r=0"
              tree = load_page(outurl_id)
              getny_dtl(tree,schema)
          except:
              print "Go to new page failed"

      schema['inurl'].append(url)
      schema['outurl'].append(outurl)
      schema['type'].append(tp)
      schema['author'].append(w)
      return schema

#load cnn page
def load_cnn(url,schema):
    tree = load_page(url)
    h_xpath='//h1/text()'
    pg_xpath='//*[@id="cnnContentContainer"]/div[4]/p'
    headline = tree.xpath(h_xpath).pop()
    paragraphs = tree.xpath(pg_xpath)
    type=tree.xpath('/html/@itemtype')[0]
    outurl=tree.docinfo.URL
    w=tree.xpath("//div[@class='cnnByline']/strong/text()")[0].split(" and ")
    #Add author and possibly co-author
    if len(w) == 1:
        schema['author'].append(w[0].replace(',',''))
    elif len(w) != 1:
        schema['author'].append(w[0].replace(',',''))
        schema['co-author'].append(w[1].replace(',',''))
    i=0
    for p in paragraphs:
        try:
            paragraph = p.xpath('text()')[0]
            schema['id'].append(i)
            schema['headline'].append(headline)
            schema['type'].append(type)
            schema['inurl'].append(url)
            schema['outurl'].append(outurl)
            schema['paragraph'].append(paragraph)
            i += 1
        except:
            print "no text found"
    return schema


def load_ap(url,schema):
    tree=load_page(url)
    h=tree.xpath('//h1[@id="page-title"]/text()')[0]
    outurl = tree.docinfo.URL
    a=tree.xpath('//div[@class="article-data"]/div/div/div/a/text()')[0]
    type="news"
    pgs=tree.xpath('//p')
    #add global vars to schema
    schema['headline'].append(h)
    schema['author'].append(a)
    schema['type'].append(type)
    schema['outurl'].append(outurl)
    schema['inurl'].append(url)
    for p in pgs:
        paragraph=p.xpath('text()')
        if len(paragraph) != 0:
            try:
                schema['paragraph'].append(paragraph[0])
            except IndexError:
                print "No Text Found"
    return schema


def load_nybooks(url,schema):
    tree = load_page(url)
    h = tree.xpath("//h2/text()")[0]
    a = tree.xpath("//h3/a/text()")[0]
    pgs = tree.xpath("//div[@id='article-body']/p")
    type = "news"
    outurl = tree.docinfo.URL
    schema['headline'].append(h)
    schema['author'].append(a)
    schema['type'].append(type)
    schema['outurl'].append(outurl)
    schema['inurl'].append(url)
    for p in pgs:
        try:
            paragraph = p.xpath("text()")[0]
            schema['paragraph'].append(paragraph)
        except IndexError:
            pass
    return schema

def load_guardian(url,schema):
    tree = load_page(url)
    h = tree.xpath("//div[@id='main-article-info']/h1/text()")[0]
    type = "news"
    outurl = tree.docinfo.URL
    author=tree.xpath('//div[@class="contributor-full"]/text()')[0].strip()
    pgs = tree.xpath("//div[@id='article-body-blocks']/p")
    schema['headline'].append(h)
    schema['type'].append(type)
    schema['inurl'].append(url)
    schema['outurl'].append(outurl)
    schema['author'].append(author)
    i=0
    for p in pgs:
        etree.strip_tags(p,'a','c')
        paragraph = "".join(p.xpath("text()"))
        try:
            i+=1
            schema['id'].append(i)
            schema['paragraph'].append(paragraph)
        except IndexError:
            pass
    return schema

def load_washpost(url,schema):
    tree = load_page(url)
    h=tree.xpath("//span[@class='entry-title']/text()")[0]
    a=tree.xpath("//a[@rel='author']/text()")[0]
    pgs = tree.xpath("//div[@id='article_body']/div/article/p")
    outurl = tree.docinfo.URL
    type="news"
    schema['headline'].append(h)
    schema['type'].append(type)
    schema['inurl'].append(url)
    schema['outurl'].append(outurl)
    schema['author'].append(a)
    i=0
    for p in pgs:
        etree.strip_tags(p,'a','c')
        paragraph = "".join(p.xpath("text()"))
        try:
            i+=1
            schema['id'].append(i)
            schema['paragraph'].append(paragraph)
        except IndexError:
            pass
    return schema

def find_text(url):
    tree = load_page(url)
    c=defaultdict(int)
    l=defaultdict(int)
    ps = tree.xpath("//p")
    for p in ps:
        e=p.getparent().tag
        try:
            l[e]+=len(p.xpath("text()")[0])
        except IndexError:
            pass
        c[e]+=1
    nrm=defaultdict(int)
    print c
    print l
    for k,v in c.items():
        if v > 4:
            nrm[k] = l[k]/v
    #decide which element, and then figure out which class or id of the element
    return nrm
