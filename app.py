#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import with_statement
from contextlib import closing
import redis
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from score_story import get_parameters,score,process_story,top5


# configuration
SECRET_KEY = 'development key'
REDIS_DB = 1
REDIS_PORT = 6379
REDIS_HOST = 'localhost'

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

@app.route('/')
def show_entries():
    uid = session.get('uid')
    entries = {'idlist':[],'alllist':[]}
    #temporary: get cnn keys
    keys_cnn = r.keys("news:cnn:*:headline")
    list_cnn = list()
    for key in keys_cnn:
        k=int(key.split(":")[2])
        list_cnn.append(k)

    id_avail = map(int,list(r.sdiff('news:nytimes:sid', 'user:%s:read:sids' %uid)))
    id_avail.sort()
    id_avail.reverse()
    l_id=len(id_avail)
    idlist=list()
    done = False
    i=0
    while not done:
        #temporary check if nytimes story exists and add
        key=id_avail[i]
        i+=1
        if key not in list_cnn:
            idlist.append(int(key))
            if len(idlist)==30:
                done=True

    alllist = map(int,list(r.smembers('news:nytimes:sid')))
    entries['idlist'].append(idlist)
    entries['alllist'].append(alllist)
    print entries['idlist']
    return render_template('show_entries.html', entries=entries, r = r)

#Called by: show_entries.html
#Calls: show_stories.html
#Gets number of paragraphs in a story
@app.route('/full/<int:sid>',methods=['POST','GET'])
def show_stories(sid):
   if not session.get('logged_in'):
      abort(401)
   print "show stories()"
   nst = len(r.keys("news:nytimes:%s:paragraph_*" % sid))
   entries = {'sid':[],'nst':[]}
   entries['sid'].append(sid)
   entries['nst'].append(nst)
   return render_template('show_stories.html', entries = entries, r=r)

@app.route('/submit', methods=['POST'])
def submit_score():
   sid = request.form['sid']
   uid = session.get('uid')
   r.sadd('user:%s:read:sids' % uid, sid)
   nst = len(r.keys("news:nytimes:%s:paragraph_*" % sid))
   for i in range(1,nst):
      score = request.form['%s:paragraph_%s' % (sid,i)]
      r.sadd('nytimes:usps:%s:%s:%s' % (uid,sid,i), score)
   return redirect(url_for('show_entries'))    

@app.route('/story/<int:sid>', methods = ['POST','GET'])
def abridged(sid):
   entries = {'sid':[],'top5':[]}
   story = process_story(sid)
   t =top5(story)
   entries['sid'].append(sid)
   for i in t:
      entries['top5'].append(i[0])
   print entries
   return render_template('show_abridged.html', entries = entries, r=r)

#Called by: show_all_stories.html
#Calls: show_abridged.html
@app.route('/all', methods=['POST'])
def read_abridged():
   if not session.get('logged_in'):
      abort(401)
   sid = request.form['abr-stories']
   entries = {'sid':[],'top5':[]}
   story = process_story(sid)
   t =top5(story)
   entries['sid'].append(sid)
   for i in t:
      entries['top5'].append(i[0])
   print entries
   return render_template('show_abridged.html', entries = entries, r=r)

#Post the non-expired story ids
@app.route('/all')
def read_stories():
   uid = session.get('uid')
   #temporary: get cnn keys
   keys_cnn = r.keys("news:cnn:*:headline")
   list_cnn = list()
   for key in keys_cnn:
       k=int(key.split(":")[2])
       list_cnn.append(k)
   list_cnn.append(305)
   entries = {'cur_ids':[]}
   #Get current stories
   cur_keys = r.keys("news:active:*")
   cur_keys_list = list()
   for key in cur_keys:
       val = int(key.split(':')[2])
       if val != 305:
          cur_keys_list.append(val)

   cur_keys_list = map(int,list(set(cur_keys_list) - set(list_cnn)))
   cur_keys_list.sort()
   cur_keys_list.reverse()

   entries['cur_ids'].append(cur_keys_list)
   print "read_stories()"
   print cur_keys_list
   return render_template('show_all_stories.html', entries=entries, r = r)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] not in r.smembers('users'):
            error = 'Invalid username'
        elif request.form['password'] != r.get('pw:%s' % request.form['username']):
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            session['uid'] = r.get('uid:%s' % request.form['username'])
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

@app.route('/home')
def homepage():
    error = None
    return render_template('homepage.html', error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
