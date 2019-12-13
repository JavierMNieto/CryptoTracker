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
import sys
import ccxt
import requests
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

    try:
        group = session.getGroup(group)
    except Http404 as e:
        group = session.addGroup(group)
    
    return group.addNode(reqData.get("name", ""), reqData.get("addr", ""), getFilters(reqData))

def delete(reqData, session):
    group = session.getGroup(reqData.get("prevCat", ""))

    return group.delNode(reqData.get("addr", ""))

def edit(reqData, session):
    if delete(reqData, session) == "Success" and add(reqData, session) == "Success":
        return "Success"
    
    return "ERROR"

def editCat(reqData, session):
    group = session.getGroup(reqData.get("cat", ""))
    if group.name != reqData.get("newCat", ""):
        group.setName(reqData.get("newCat", ""))

    group.setFilters(getFilters(reqData),)

    return "Success"

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
	return JsonResponse(request.user.getCoin(coin).isUniqSession(request.GET.get("name")), safe=False)

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
    TODO: Better Filter Efficiency by only adding custom filters instead of removing defaults
"""
def getFilters(reqData):
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
    return filters

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
