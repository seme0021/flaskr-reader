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

    idlist = list(r.sdiff('news:nytimes:sid', 'user:%s:read:sids' %uid))
    alllist = list(r.smembers('news:nytimes:sid'))
    entries['idlist'].append(idlist)
    entries['alllist'].append(alllist)
    print entries['idlist']
    return render_template('show_entries.html', entries=entries, r = r)

#Called by: show_entries.html
#Calls: show_stories.html
#Gets number of paragraphs in a story
@app.route('/',methods=['POST'])
def show_stories():
   if not session.get('logged_in'):
      abort(401)
   print "show stories()"
   sid = request.form['stories']
   nst = len(r.keys("news:nytimes:%s:paragraph_*" % sid))
   entries = {'sid':[],'nst':[]}
   entries['sid'].append(sid)
   entries['nst'].append(nst)
   return render_template('show_stories.html', entries = entries, r=r)

@app.route('/submit', methods=['POST'])
def submit_score():
   sid = request.form['sid']
   uid = session.get('uid')
   r.sadd('user:%s:read:sids' % 1, sid)
   nst = len(r.keys("news:nytimes:%s:paragraph_*" % sid))
   for i in range(1,nst):
      score = request.form['%s:paragraph_%s' % (sid,i)]
      r.sadd('nytimes:usps:%s:%s:%s' % (uid,sid,i), score)
   return redirect(url_for('show_entries'))    

#Called by: show_all_stories.html
#Calls: show_abridged.html
@app.route('/all', methods=['POST'])
def read_abridged():
   if not session.get('logged_in'):
      abort(401)
   sid = request.form['abr-stories']
   entries = {'sid':[],'top5':[]}

   print str(sid)
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
   entries = {'idlist':[],'alllist':[],'cur_ids':[]}
   #Get current stories
   cur_keys = r.keys("news:active:*")
   for key in cur_keys:
       entries['cur_ids'].append(key.split(':')[2])
   idlist = list(r.sdiff('news:nytimes:sid', 'user:%s:read:sids' %uid))
   alllist = list(r.smembers('news:nytimes:sid'))
   entries['idlist'].append(idlist)
   entries['alllist'].append(alllist)
   print "read_stories()"
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
