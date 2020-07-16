from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404
from django.template import loader
from django.shortcuts import get_object_or_404, render, redirect
from neo4j.v1 import GraphDatabase
from django.core.exceptions import ValidationError
from urllib.parse import unquote
from pyvis.network import Network
from .clean import *
from .defaults import *
from .models import Coin
from .query import CoinController
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

coinController = CoinController()

coins = ["USDT"]

"""
    TODO: Maybe use class view instead for more organised url/function mapping
"""

def home(request, coin=None):
    btc = ccxt.coinbase().fetch_ticker('BTC/USD')

    sessions      = request.user.getCoin(coin).get_sessions()
    basic_session = Coin.objects.filter(name__iexact=coin).first().sessions.first().get_as_dict()
    return render(request, 'tracker/index.html', {'search': [], 'coin': 'home', 'btc': btc, 'basic_session': basic_session, 'sessions': sessions, 'session': None})

def session(request, coin=None, session_id=None):
	session = request.user.getCoin(coin).get_session(session_id).name

	btc = ccxt.coinbase().fetch_ticker('BTC/USD')

	search = {'coin': coin, 'btc': btc, 'dFilters': Filters().get_formatted_filters(), 'session': session}
	return render(request, 'tracker/index.html', search)

def go_to_default_session(request, coin):
    return redirect(Coin.objects.filter(name__iexact=coin).first().sessions.first().get_url())

def get_known(request, coin=None, session_id=None):
    return JsonResponse(request.user.getCoin(coin).get_session(session_id).get_as_list(), safe=False) 

def add(req_data, session):
    group   = req_data.get("cat", "")

    group = session.addGroup(group)
    
    return group.addNode(req_data.get("name", ""), req_data.get("addr", ""), get_filters(req_data, format=False))

def delete(req_data, session):
    group = session.get_group(req_data.get("prevCat", ""))

    return group.delNode(req_data.get("addr", ""))

def edit(req_data, session):
    delete(req_data, session)
    add(req_data, session)

    return "Successfully edited node."

def edit_cat(req_data, session):
    group = session.get_group(req_data.get("cat", ""))
    if group.name != req_data.get("newCat", ""):
        group.setName(req_data.get("newCat", ""))

    group.setFilters(get_filters(req_data, format=False),)

    return "Successfully edited group."

methods = {
    "add": add,
    "delete": delete,
    "edit": edit,
    "edit_cat": edit_cat
}

def change(request, coin=None, session_id=None):
    if request.method != "POST":
        raise Http404('Only POSTs are allowed!')

    method = request.POST.get('method', '')

    resp = "ERROR"

    try:
        if method in methods:
            resp = methods[method](request.POST, request.user.getCoin(coin).get_session(session_id))
    except ValidationError as e:
        resp = "ERROR! " + e.message
    except Exception as e:
        print(e)

    return JsonResponse(resp, safe=False)

def addr(request, coin=None, session_id=None, addr=None):
    session = request.user.getCoin(coin).get_session(session_id)

    data = coinController.get_addr(addr, session, get_filters(request.GET))
    return render(request, 'coin/coin.html', data)

def custom_group(request, coin=None, session_id=None):
    session = request.user.getCoin(coin).get_session(session_id)
    
    data = coinController.get_group(session, get_filters(request.GET), addrs=request.GET.getlist("addr[]", None))
    data['session'] = session.name
    return render(request, 'coin/coin.html', data)

def group(request, coin=None, session_id=None, group_id=None):
    session = request.user.getCoin(coin).get_session(session_id)
    
    data = coinController.get_group(session, get_filters(request.GET), group_id)
    data['session'] = session.name
    return render(request, 'coin/coin.html', data)

def get_txs(request, coin=None, session_id=None):
    if request.method != "GET":
        raise Http404("Only GETs are allowed!")

    return JsonResponse(coinController.get_txs(request.user.getCoin(coin).get_session(session_id), get_params(request.GET), get_filters(request.GET)), safe=False)

def get_graph_data(request, coin=None, session_id=None):   
    if request.method != "GET":
        raise Http404("Only GETs are allowed!") 
    return JsonResponse(coinController.get_graph_data(request.user.getCoin(coin).get_session(session_id), get_params(request.GET), get_filters(request.GET), request.GET.get("lastId", 0)), safe=False)

def get_tx(request, tx, coin=None):
    if request.method != "GET":
        raise Http404("Only GETs are allowed!")

    if request.GET.get("rawTx"):
        return JsonResponse(get_blockchain("omni_gettransaction", [tx]), json_dumps_params={'indent': 2})
    return render(request, 'coin/tx.html', get_blockchain("omni_gettransaction", [tx]))

def is_uniq_session(request, coin=None):
    uniq = True

    try:
        request.user.getCoin(coin).is_uniq_session(request.GET.get("name"))
    except ValidationError as e:
        uniq = True
    
    return JsonResponse(uniq, safe=False)

def is_valid_addr(request, coin=None):
    if request.method != "GET":
        raise Http404("Only GETs are allowed!")
    return JsonResponse(coinController.is_valid_addr(coin, request.GET.get('addr')), safe=False)

def copy_session(request, coin=None, session_id=None):
    if request.method != "POST":
        raise Http404("Only POSTs are allowed!")
    
    if request.user.is_authenticated and request.user.settings.premium:
        session = request.user.getCoin(coin).add_session(request.POST.get("name", ""), copy_session=session_id)
        
        if session:
            return JsonResponse(session.getUrl(), safe=False)

    return JsonResponse("ERROR", safe=False)

def add_session(request, coin=None):
    if request.method != "POST":
        raise Http404("Only POSTs are allowed!")
    
    if request.user.is_authenticated and request.user.settings.premium:
        session = request.user.getCoin(coin).add_session(request.POST.get("name", ""))

        if session:
            return JsonResponse(session.getUrl(), safe=False)

    return JsonResponse("ERROR", safe=False)

def del_session(request, coin=None):
    if request.method != "POST":
        raise Http404("Only POSTs are allowed!")

    if request.user.is_authenticated and request.user.settings.premium:
        return JsonResponse(request.user.getCoin(coin).del_session(request.POST.get("session_id", "")), safe=False)
    
    return JsonResponse("ERROR", safe=False)

def edit_session(request, coin=None):
    if request.method != "POST":
        raise Http404("Only POSTs are allowed!")

    if request.user.is_authenticated and request.user.settings.premium:
        return JsonResponse(request.user.getCoin(coin).edit_session(request.POST.get("session_id", ""), request.POST.get("name", "")), safe=False)
    
    return JsonResponse("ERROR", safe=False)

"""
    TODO: Better Filter Efficiency by only adding custom filters instead of replacing defaults
"""
def get_filters(req_data, format=True):
    filters = DFilters()
    for f, val in filters.items():
        temp = req_data.get(f)
        
        if temp and temp != "max" and temp != "latest" and temp != "min" and temp != "oldest":
            try:
                temp = float(temp.replace(" ", ""))
            except Exception:
                if "max" in f or "min" in f:
                    continue

            filters[f] = temp
    
    if format:
        return Filters(filters).get_raw_filters()

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

def get_params(req_data):
    params = DParams()
    for p, val in params.items():
        temp = None

        if '[]' in p:
            temp = req_data.getlist(p)
        else:
            temp = req_data.get(p)

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
	Return info from directly blockchain
"""
def get_blockchain(method, params=[]):
    data = {"method": method, "params": params, "jsonrpc": "1.0"}
    return (requests.post("http://127.0.0.1:8332/", auth=Auth(), data=json.dumps(data), headers={'content-type': 'application/json'}).json())['result']
