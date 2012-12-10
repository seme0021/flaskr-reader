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
SALT = 'retwis'


app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

@app.route('/')
def show_entries():
    idlist = list(r.smembers('news:nytimes:sid'))
    print "Hello"
    return render_template('show_entries.html', idlist = idlist, r = r)

@app.route('/',methods=['POST'])
def show_stories():
   sid = request.form['stories']
   nst = len(r.keys("news:nytimes:%s:paragraph_*" % sid))
   entries = {'sid':[],'nst':[]}
   entries['sid'].append(sid)
   entries['nst'].append(nst)
   return render_template('show_stories.html', entries = entries, r=r)

@app.route('/', methods=['POST'])
def submit_score():
   return redirect(url_for('show_entries'))    
    
@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    #g.db.execute('insert into entries (title, text) values (?, ?)',
                 #[request.form['title'], request.form['text']])
    #g.db.commit()
    title = request.form['title']
    text = request.form['text']
    id = r.incr('global:LatestEntryId')
    r.lpush('idlist', id)
    r.set('entries:%s:title' % id, '%s' % title)
    r.set('entries:%s:text' % id, '%s' % text)
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
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
