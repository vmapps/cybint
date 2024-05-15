#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --------------------------------------------------
# Imports
# --------------------------------------------------

from flask import Flask, render_template, request, session, flash, make_response, redirect, url_for

import datetime
import nltk
import os
import pymongo
import sys

import utils

# --------------------------------------------------
# Init
# --------------------------------------------------

# nltk.download('punkt')
root = os.path.dirname(__file__)

# load configuration file
config = utils.loadConfig(root+'/config/config.yml')

# setup flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'super secret key you will never guess'
app.config['STATIC_FOLDER'] = 'static'
app.config['PROJECTS'] = []
app.config['app'] = config['app']

@app.template_filter('fromtimestamp')
def _filter_fromtimestamp(ts):
    dt = datetime.datetime.fromtimestamp(ts)
    return dt

# Database connector to Mongo
mongo = pymongo.MongoClient(
    host = config['mongo']['host'],
    port = config['mongo']['port'],
    serverSelectionTimeoutMS = config['mongo']['timeout']
)

try:
    mongo.list_databases()
except Exception as e:
    print('[ERROR] could not connect to mongo database',file=sys.stderr)
    sys.exit(1)

# setup NLTK
nltk.data.path.append(root+'/../nltk_data/')

# initialize projects
app.config['PROJECTS'] = utils.initProjects(mongo,root+'/config/projects')

# --------------------------------------------------
# Decorators
# --------------------------------------------------

@app.before_request
def before_request_func():

    if not 'project' in session:
        session['project'] = 'default'

    global db
    
    db = mongo['cybint_{}'.format(session['project'])]

    # make sure not handling calls to static path
    if (request.path).split('/')[1] != app.config['STATIC_FOLDER'] :

        # check if database ping is ok
        try:
            with pymongo.timeout(3):
                db.command('ping')
        # if connection fails then display error page 
        except pymongo.errors.ConnectionFailure:
            return render_template('error.jinja',message='Error connecting to Mongo database')
    
# --------------------------------------------------
# Routes
# --------------------------------------------------

#
# Index
#
@app.route('/')
def index():

    items = []
    for obj_a in db['articles'].find().limit(5).sort('__imported',pymongo.DESCENDING):
        items.append(obj_a)

    # return redirect(url_for('feeds'))
    return render_template('index.jinja',data=items)

#
# Error
#
@app.route('/error')
def error():
    message = request.args.get('message')
    return render_template('error.jinja',message=message)

#
# Projects
#
@app.route('/projects/')
@app.route('/projects/<id>')
def projects(id=None):

    # set project into session
    if id and id.isalnum():
        if id in app.config['PROJECTS']:
            session['project'] = id
            return {'status':'set'}
        else:
            session['project'] = 'default'
            return {'status':'error'}
    # return projects
    else:
        return app.config['PROJECTS']

#
# Feeds
#
@app.route('/feeds',methods=['GET','PUT','DELETE'])
def feeds():
    
    # Get feeds
    if request.method == 'GET':

        items = []

        keys = db['feeds'].find().sort('id',pymongo.ASCENDING)
        for obj in keys:

            articles = db['articles'].find({'__feed':obj['id']})
            obj['articles'] = len(list(articles))

            items.append(obj)

        return render_template('feeds.jinja',data=items)

    # Set feed as active
    if request.method == 'PUT':

        id = request.json['id']
        db['feeds'].update_one({'id':id},{'$set':{'enable':True}})

        return {'status':'set'}

    # Unset active feed 
    if request.method == 'DELETE':

        id = request.json['id']
        db['feeds'].update_one({'id':id},{'$set':{'enable':False}})

        return {'status':'unset'}

#
# Articles
#
@app.route('/articles',methods=['GET'])
def articles():

    word = request.args.get('keyword')
    feed = request.args.get('feed')

    items = []
    for obj_a in db['articles'].find().sort('__imported',pymongo.DESCENDING):

        # if searching by word, skip articles not matching
        if word and obj_a['title'].lower().find(word.lower())==-1:
            continue

        # if searching by feed, skip articles not matching
        if feed and obj_a['__feed']!=feed:
            continue

        items.append(obj_a)

    return render_template('articles.jinja',data=items)

#
# Search (TODO)
#
@app.route('/search',methods=['GET'])
def search():

    keyword = request.args.get('q')

    results = db['articles'].find(
        {'$or':[
            {'title':{'$regex':keyword,'$options':'i'}},
            {'summary':{'$regex':keyword,'$options':'i'}}
        ]}).sort('__imported',pymongo.DESCENDING)

    items = []
    for obj_a in results:
        items.append(obj_a)

    return render_template('articles.jinja',data=items)

#
# Keywords
#
@app.route('/keywords')
def keywords():
  
    stats = dict()
    for obj in db['articles'].find():
        
        words = nltk.tokenize.word_tokenize(obj['title'].lower())
        tags = nltk.tag.pos_tag(words)

        # for word in words:
        for (word,tag) in tags:

            # skip if not a noun
            if not tag in config['keywords']['tags'] :
                continue
        
            if word in stats: 
                stats[word] = stats[word] + 1
            else:
                stats[word] = 1

    min_length     = config['keywords']['min_length']
    min_occurences = config['keywords']['min_occurences']

    print(min_length,min_occurences)

    stats = dict(filter(lambda occ: len(occ[0])>min_length, stats.items()))
    stats = dict(filter(lambda occ: occ[1]>min_occurences, stats.items()))

    stats = dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

    return render_template('keywords.jinja',data=stats)

#
# Bookmarks
#
@app.route('/bookmarks',methods=['GET','PUT','DELETE'])
def bookmarks():

    # Get bookmarks
    if request.method == 'GET':

        items = []
        # for obj_a in db['articles'].find({'__bookmark':True}):
        for obj_a in db['bookmarks'].find():
            items.append(obj_a)

        # flash('Bookmarks loaded','success')
        return render_template('bookmarks.jinja',data=items)

    # Set bookmark
    if request.method == 'PUT':

        hash = request.json['hash']
        db['articles'].update_one({'__hash':hash},{'$set':{'__bookmark':True}})

        # check if articles already saved in bookmarks
        res = db['bookmarks'].find({'__hash':hash},{'_id':1})

        if not len(list(res)):
            obj_a = db['articles'].find_one({'__hash':hash})
            db['bookmarks'].insert_one(obj_a)

        return {'status':'set'}

    # Unset bookmark
    if request.method == 'DELETE':

        hash = request.json['hash']
        # db['articles'].update_one({'__hash':hash},{'$unset':{'__bookmark':''}})
        db['articles'].update_one({'__hash':hash},{'$set':{'__bookmark':False}})
        db['bookmarks'].delete_one({'__hash':hash})

        return {'status':'unset'}

# --------------------------------------------------
# Only for developpment purpose 
# --------------------------------------------------

if __name__ == "__main__":
    
    app_debug     = True
    app_bind      = '0.0.0.0'
    app_port      = 8000
    app_threaded  = True

    app.run(debug=app_debug, host=app_bind, port=app_port, threaded=app_threaded)

# --------------------------------------------------
