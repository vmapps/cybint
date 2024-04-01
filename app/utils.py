#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --------------------------------------------------
# Imports
# --------------------------------------------------

import colored
import csv
import datetime
import feedparser
import glob
import hashlib
import os
import pathlib
import socket
import yaml

# --------------------------------------------------
# Functions
# --------------------------------------------------

#
# Load config file
#
def loadConfig(filename):

    # print('[INFO] loading configuraion file ...')

    with open(filename,'r') as yamlfile:
        cfg = yaml.load(yamlfile, Loader=yaml.FullLoader)

    return cfg

#
# Get hash from string
#
def getHash(buffer):
    
    buffer = str(buffer).encode('utf-8')
    hash = hashlib.md5(buffer).hexdigest()

    return hash

#
# Get current datetime
#
def getNow():

    now = datetime.datetime.now()
    dt = str(now).split('.')[0]

    return dt

#
# Initialize projects
#
def initProjects(mongoc,folder):

    print('[INFO] initializing databases ...')

    # get list of projects
    projects = []
    feeds = glob.glob(folder+'/*.feeds')
    for f in feeds:
        p = pathlib.Path(f).stem
        projects.append(p)

        print('[INFO] setting up project {} ...'.format(p))
        store = mongoc['cybint_{}'.format(p)]

        importFeeds(store,f)
        importArticles(store)

    # create crontab to update projects
    if os.path.exists('/etc/crontabs/'):
        
        print('[INFO] setting up crontab ...')

        cron = open('/etc/crontabs/daemon', 'w')
        cron.write('# crontab for cybint\n')
        for p in projects:
            cron.write('*/10    *   *   *   *   python3 /cybint/manage.py --project {} --articles >/dev/null 2>&1\n'.format(p))
        cron.close()

    return projects

#
# Clean database
#
def flushDatabase(db):

    print('[INFO] flushing database ...')

    db['feeds'].drop()
    db['articles'].drop()
    db['bookmarks'].drop()

#
# Import feeds into database
#
def importFeeds(db,feeds):

    print('[INFO] loading feeds file ...')

    with open(feeds, newline='') as fh:

        feeds = csv.reader(fh, delimiter=',')
        for feed in feeds:
            item = {
                'id': feed[0],
                'title': feed[1],
                'url': feed[2],
                'created': getNow(),
                'enable': True,
            }

            if feed[0][0]=='#':
                item['id'] = item['id'][1:]
                item['enable'] = False
            
            if not db['feeds'].find_one({'id':item['id']}):
                db['feeds'].insert_one(item)
    
    return True

#
# Import articles into database
#
def importArticles(db):

    print('[INFO] getting feeds content ...')
    res = db['feeds'].find().sort('id',1)

    for idx,obj in enumerate(res):

        if not obj['enable']:
            continue

        # get items from feed
        articles = getRss(obj['url'])

        # save articles  to database
        saveArticles(db,obj['id'],obj['title'], articles)

        print('#{} - Got {} articles from feed "{}" at {}'.format(idx,len(articles),obj['id'],obj['url']))

    return True

#
# Get RSS content
#
def getRss(url):

    socket.setdefaulttimeout(10)
 
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'fr,en-US;q=0.9,en;q=0.8',
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Cache-control': 'no-cache',
    }

    # feedparser.USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
   
    try:
        response = feedparser.parse(url,request_headers=headers)
        return response.entries
    except Exception as error:
        print('Error:',error)
        return []

#
# Save RSS articles into database
#
def saveArticles(db,prefix,source,items):
    
    for idx,item in enumerate(items):

        hash = getHash(item['title'])

        item['__hash'] = hash
        item['__feed'] = prefix
        item['__source'] = source
        item['__bookmark'] = False

        res = db['articles'].find({'__hash':hash},{'_id':1})

        if len(list(res)):
            # print(colored.Fore.red,'\tContent already exists\t',end='')
            continue
        else:
            # print(colored.Fore.green,'\tAdding new content\t',end='')
            db['articles'].insert_one(item)

        print('',prefix,idx,sep='\t',end='')
        print(colored.Fore.green,'\tAdding new content\t',end='')
        print(colored.Style.reset,item['title'][:75],'...',sep=' ')

    return True

# --------------------------------------------------
