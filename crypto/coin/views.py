from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404
from django.template import loader
from django.shortcuts import get_object_or_404, render, redirect
from neo4j.v1 import GraphDatabase
from django.core.exceptions import ValidationError
import pprint
import json
import math
import time
import datetime
import sys
import ccxt
import re
import requests
import traceback
from .models import Coin
from urllib.parse import unquote
from pyvis.network import Network

from .query import CoinController

sys.path.append("../")
from static.py.defaults import *
from static.py.clean import *

coinController = CoinController()

coins = ["USDT"]

def home(request, coin=None):
    btc = ccxt.coinmarketcap().fetch_ticker('BTC/USD')

    sessions      = request.user.getCoin(coin).getSessions()
    basic_session = Coin.objects.filter(name__iexact=coin).first().sessions.first().getAsDict()
    return render(request, 'tracker/index.html', {'search': [], 'coin': 'home', 'btc': btc, 'basic_session': basic_session, 'sessions': sessions, 'session': None})

def session(request, coin=None, session_id=None):
	session = request.user.getCoin(coin).getSession(session_id).name

	btc = ccxt.coinmarketcap().fetch_ticker('BTC/USD')

	search = {'coin': coin, 'btc': btc, 'dFilters': Filters().getFormattedFilters(), 'session': session}
	return render(request, 'tracker/index.html', search)

def goToDefaultSession(request, coin):
    return redirect(Coin.objects.filter(name__iexact=coin).first().sessions.first().getUrl())

def getKnown(request, coin=None, session_id=None):
    return JsonResponse(request.user.getCoin(coin).getSession(session_id).getAsList(), safe=False) 

def add(reqData, session):
    group   = reqData.get("cat", "")

    group = session.addGroup(group)
    
    return group.addNode(reqData.get("name", ""), reqData.get("addr", ""), getFilters(reqData, format=False))

def delete(reqData, session):
    group = session.getGroup(reqData.get("prevCat", ""))

    return group.delNode(reqData.get("addr", ""))

def edit(reqData, session):
    delete(reqData, session)
    add(reqData, session)

    return "Successfully edited node."

def editCat(reqData, session):
    group = session.getGroup(reqData.get("cat", ""))
    if group.name != reqData.get("newCat", ""):
        group.setName(reqData.get("newCat", ""))

    group.setFilters(getFilters(reqData, format=False),)

    return "Successfully edited group."

methods = {
    "add": add,
    "delete": delete,
    "edit": edit,
    "editCat": editCat
}

def change(request, coin=None, session_id=None):
    if request.method != "POST":
        raise Http404('Only POSTs are allowed!')

    method = request.POST.get('method', '')

    resp = "ERROR"

    try:
        if method in methods:
            resp = methods[method](request.POST, request.user.getCoin(coin).getSession(session_id))
    except ValidationError as e:
        resp = "ERROR! " + e.message
    except Exception as e:
        print(e)

    return JsonResponse(resp, safe=False)

def addr(request, coin=None, session_id=None, addr=None):
    session = request.user.getCoin(coin).getSession(session_id)

    data = coinController.getAddr(addr, session, getFilters(request.GET))
    return render(request, 'coin/coin.html', data)

def customGroup(request, coin=None, session_id=None):
    session = request.user.getCoin(coin).getSession(session_id)
    
    data = coinController.getGroup(session, getFilters(request.GET), addrs=request.GET.getlist("addr[]", None))
    data['session'] = session.name
    return render(request, 'coin/coin.html', data)

def group(request, coin=None, session_id=None, group_id=None):
    session = request.user.getCoin(coin).getSession(session_id)
    
    data = coinController.getGroup(session, getFilters(request.GET), group_id)
    data['session'] = session.name
    return render(request, 'coin/coin.html', data)

def getTxs(request, coin=None, session_id=None):
    if request.method != "GET":
        raise Http404("Only GETs are allowed!")

    return JsonResponse(coinController.getTxs(request.user.getCoin(coin).getSession(session_id), getParams(request.GET), getFilters(request.GET)), safe=False)

def getGraphData(request, coin=None, session_id=None):   
    if request.method != "GET":
        raise Http404("Only GETs are allowed!") 
    return JsonResponse(coinController.getGraphData(request.user.getCoin(coin).getSession(session_id), getParams(request.GET), getFilters(request.GET), request.GET.get("lastId", 0)), safe=False)

def getTx(request, tx, coin=None):
    if request.method != "GET":
        raise Http404("Only GETs are allowed!")

    if request.GET.get("rawTx"):
        return JsonResponse(getBlockchain("omni_gettransaction", [tx]), json_dumps_params={'indent': 2})
    return render(request, 'coin/tx.html', getBlockchain("omni_gettransaction", [tx]))

def isUniqSession(request, coin=None):
    uniq = True

    try:
        request.user.getCoin(coin).isUniqSession(request.GET.get("name"))
    except ValidationError as e:
        uniq = True
    
    return JsonResponse(uniq, safe=False)

def isValidAddr(request, coin=None):
    if request.method != "GET":
        raise Http404("Only GETs are allowed!")
    return JsonResponse(coinController.isValidAddr(coin, request.GET.get('addr')), safe=False)

def copySession(request, coin=None, session_id=None):
    if request.method != "POST":
        raise Http404("Only POSTs are allowed!")
    
    if request.user.is_authenticated and request.user.settings.premium:
        session = request.user.getCoin(coin).addSession(request.POST.get("name", ""), copySession=session_id)
        
        if session:
            return JsonResponse(session.getUrl(), safe=False)

    return JsonResponse("ERROR", safe=False)

def addSession(request, coin=None):
    if request.method != "POST":
        raise Http404("Only POSTs are allowed!")
    
    if request.user.is_authenticated and request.user.settings.premium:
        session = request.user.getCoin(coin).addSession(request.POST.get("name", ""))

        if session:
            return JsonResponse(session.getUrl(), safe=False)

    return JsonResponse("ERROR", safe=False)

def delSession(request, coin=None):
    if request.method != "POST":
        raise Http404("Only POSTs are allowed!")

    if request.user.is_authenticated and request.user.settings.premium:
        return JsonResponse(request.user.getCoin(coin).delSession(request.POST.get("session_id", "")), safe=False)
    
    return JsonResponse("ERROR", safe=False)

def editSession(request, coin=None):
    if request.method != "POST":
        raise Http404("Only POSTs are allowed!")

    if request.user.is_authenticated and request.user.settings.premium:
        return JsonResponse(request.user.getCoin(coin).editSession(request.POST.get("session_id", ""), request.POST.get("name", "")), safe=False)
    
    return JsonResponse("ERROR", safe=False)

"""
    TODO: Better Filter Efficiency by only adding custom filters instead of replacing defaults
"""
def getFilters(reqData, format=True):
    filters = DFilters()
    for f, val in filters.items():
        temp = reqData.get(f)
        
        if temp and temp != "max" and temp != "latest" and temp != "min" and temp != "oldest":
            try:
                temp = float(temp.replace(" ", ""))
            except Exception:
                if "max" in f or "min" in f:
                    continue

            filters[f] = temp
    
    if format:
        return Filters(filters).getRawFilters()

    return filters

"""
conversionToHours = {
    "second": 1/3600,
    "minute": 1/60,
    "hour": 1,
    "day": 24,
    "week": 7*24,
    "month": 30*24,
    "year": 365*24
}

def convertToHours(amt, time):
    for t, val in conversionToHours.items():
        if t in time:
            return amt*val
    
    return 0

def parseTimeRange(range):
    amt = int(re.search(r'\d+', range).group())
    hours = convertToHours(amt, range.lower())

    return -datetime.timedelta(hours=hours).total_seconds()
"""

def getParams(reqData):
    params = DParams()
    for p, val in params.items():
        temp = None

        if '[]' in p:
            temp = reqData.getlist(p)
        else:
            temp = reqData.get(p)

        if temp:
            try:
                temp = float(temp.replace(" ", ""))
                if p == 'page':
                    temp = max(int(temp), 0)
            except Exception:
                if p == "page":
                    continue
            
            if ("order" in p.lower() and val.lower() != "desc" and val.lower() != "asc") or ("sort" in p.lower() and val.lower() != "blocktime" and val.lower() != "amount" and val.lower() != "usdAmount"):
                continue

            params[p] = temp
    
    return params

"""
	Return info from blockchain
"""
def getBlockchain(method, params=[]):
    data = {"method": method, "params": params, "jsonrpc": "1.0"}
    return (requests.post("http://127.0.0.1:8332/", auth=Auth(), data=json.dumps(data), headers={'content-type': 'application/json'}).json())['result']
