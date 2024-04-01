#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --------------------------------------------------
# Imports
# --------------------------------------------------

import argparse
import os
import pathlib
import pymongo
import sys

import app.utils

# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":

    root = os.path.dirname(__file__)

    # load configuration file
    config = app.utils.loadConfig(root+'/app/config/config.yml')

    parser = argparse.ArgumentParser(
        description = config['app']['name']+' - '+config['app']['description']+' - '+config['app']['version'],
        epilog = '(c) 2024 - '+config['app']['author']+' - '+config['app']['contact']
    )

    # parser.add_argument("path")
    parser.add_argument("-i", "--init", help='init configuraiton and data', action="store_true")
    parser.add_argument("-p", "--project", help='use specific project (if none, use "default")', default='default')
    parser.add_argument("-c", "--clean", help='cleanup redis database', action="store_true")
    parser.add_argument("-f", "--feeds", help='import feeds from file', type=pathlib.Path)
    parser.add_argument("-a", "--articles", help='import content from feeds', action="store_true")

    args = parser.parse_args()
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # connect to Mongo database
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

    # Set project qnd store
    project = args.project
    if not project.isalnum():
        project = 'default'
    
    # initi projects
    if args.init:
        app.utils.initProjects(mongo,root+'/app/config/projects')
        sys.exit()

    # Set dataabse store 
    store = mongo['cybint_{}'.format(project)]

    # flush database
    if args.clean:
        app.utils.flushDatabase(store)

    # import feeds
    if args.feeds:
        store['feeds'].drop()
        app.utils.importFeeds(store,args.feeds)

    # import articles
    if args.articles:
        app.utils.importArticles(store)

# --------------------------------------------------
