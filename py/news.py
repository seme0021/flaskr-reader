import lxml.html,cookielib,urllib2
from lxml import etree
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
    outurl = tree.xpath("//link/@href")[0]
    #append first paragraph
    schema['id'].append(1)
    schema['headline'].append(headline)
    schema['type'].append(type)
    schema['inurl'].append(url)
    schema['outurl'].append(outurl)
    schema['paragraph'].append(main_p)
    i=2
    for p in pg:
        paragraph = p.xpath("text()")[0]
        schema['id'].append(i)
        schema['headline'].append(headline)
        schema['type'].append(type)
        schema['inurl'].append(url)
        schema['outurl'].append(outurl)
        schema['paragraph'].append(paragraph)
        i+=1
    return schema

def get_huff(url,schema):
    tree = load_page(url)
    pg = '//div[@class="articleBody"]/p'
    headline = tree.xpath("//h1[@class='title-news']/text()")[0]
    headline = ' '.join(headline.split())
    type = tree.xpath("//div[@id='news_content']/@itemtype")[0]
    outurl=tree.xpath("//link/@href")[2]
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
   outurl = tree.xpath('/html/@itemid')[0]
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
    outurl=tree.xpath('/html/head/meta[22]/@content')[0]
    w=tree.xpath("//div[@class='cnnByline']/strong/text()")[0].split(" and ")
    #Add author and possibly co-author
    if len(w) == 1:
        schema['author'].append(w[0])
    elif len(w) != 1:
        schema['author'].append(w[0])
        schema['co-author'].append(w[1])
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