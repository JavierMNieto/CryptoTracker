from __future__ import print_function
import os
import sys
import json
import pprint
import time
from urllib.parse import parse_qs as pq
from fnmatch import fnmatch
from traceback import print_exc

sys.path.insert(0, os.path.dirname(__file__))
from search import Search
search = Search('https://blockchain.info/rawaddr/', {'url': 'bolt://localhost:7687', 'user': 'neo4j', 'pass': '2282002'})

def load_misc(path, start_response):
    contentType = []
    message = ""
    try:
        if ".png" in path:
            message = open(path, "rb").read()
            contentType = [('Content-Type', 'image/png')]
        elif ".jpg" in path:
            message = open(path, "rb").read()
            contentType = [('Content-Type', 'image/jpg')]
        elif ".css" in path:
            message = open(path, "r").read().encode()
            contentType = [('Content-Type', 'text/css')]
        elif ".html" in path:
            message = open(path, "r").read().encode()
            contentType = [('Content-Type', 'text/html')]
        else:
            start_response('404 NOT OK', contentType + [('Cache-Control', 'no-store, must-revalidate'), ('Pragma', 'no-cache'), ('Expires', '0')])
            return "<h1> PAGE NOT FOUND </h1>".encode()
        return message
    except:
        start_response('404 NOT OK', contentType + [('Cache-Control', 'no-store, must-revalidate'), ('Pragma', 'no-cache'), ('Expires', '0')])
        return "<h1> PAGE NOT FOUND </h1>".encode()
    

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def logPrint(*args, **kwargs):
    print(*args, file=open("log.txt", "a"), **kwargs)

calls = {"getAddr": search.getAddr}

def application(environ, start_response):
    message = ("<h1>Hello World</h1> <p>" + str(environ) + "</p>")
    message += "<h1> {} </h1>".format(sys.version)
    message += "<h1> Address Info </h1>"
    req_path = environ["REQUEST_URI"].strip().split("/")[1:]
    start_response('200 OK', [('Content-Type', 'text/html')])
    print(req_path[0])
    logPrint(req_path[0])
    if req_path[0] in calls:
        st = pprint.pformat(calls[req_path[0]](environ))
        message += ('<pre style="word-wrap: break-word; white-space: pre-wrap;">' + st + "</pre>")
        message = message.encode()
        starttime = time.time()
        while True:
            print("Refresh")
            search.refresh()
            time.sleep(60.0 - ((time.time() - starttime) % 60.0))
    else:
        message = load_misc(environ["REQUEST_URI"][1:], start_response)
    return [message]
