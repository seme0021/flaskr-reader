#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import with_statement
from contextlib import closing
import redis
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

# configuration
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
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
    idlist = list(r.sdiff('news:nytimes:sid', 'user:%s:read:sids' %uid))
    return render_template('show_entries.html', idlist = idlist, r = r)

@app.route('/',methods=['POST'])
def show_stories():
   if not session.get('logged_in'):
      abort(401)
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
