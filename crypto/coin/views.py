from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from neo4j.v1 import GraphDatabase
import pprint
import json
import math
import time
from urllib.parse import unquote
from pyvis.network import Network

from .defaults import *
from .query import CoinController

coinController = CoinController()

def getTxs(request, coin=None):
    return JsonResponse(coinController.getTxs(getParams(request)), safe=False)

def getKnown(request, coin=None):
    coinController.setCoin(coin)
    return JsonResponse(coinController.getKnownList(), safe=False)

def addr(request, coin=None):
    coinController.setCoin(coin)
    
    if request.method == "GET":
        if request.GET.get('method') == "isValid":
            return JsonResponse(coinController.isValidAddr(request.GET.get('addr')), safe=False)

    if request.method != "POST":
        return "ERROR"
    
    method = request.POST.get('method') or ""
 
    if method == "add":
        return JsonResponse(coinController.addAddr(request.POST.get('addr'), request.POST.get('name'), request.POST.get('cat') or "", getParams(request, isPost=True)), safe=False)
    elif method == "edit":
        return JsonResponse(coinController.editAddr(request.POST.get('addr'), request.POST.get('name'), request.POST.get('cat') or "", getParams(request, isPost=True)), safe=False)
    elif method == "delete":
        return JsonResponse(coinController.delAddr(request.POST.get('addr')), safe=False)
    elif method == "editCat":
        return JsonResponse(coinController.editCat(request.POST.get('prevCat'), request.POST.get('newCat'), getParams(request, isPost=True)), safe=False)
    else:
        return "ERROR"

def search(request, id, coin=None):
    coinController.setCoin(coin)

    id = unquote(id)

    data = coinController.getAddrInfo(id, getParams(request))

    return render(request, 'coin/coin.html', data)

def getParams(request, isPost=False):
    coinController.setCoin(request.build_absolute_uri())
    
    params = DParams()
    for p, val in params.items():
        temp = None

        if '[]' in p:
            if isPost:
                temp = request.POST.getlist(p)
            else:
                temp = request.GET.getlist(p)
        else:
            if isPost:
                temp = request.POST.get(p)
            else:
                temp = request.GET.get(p)

        if temp and temp != "max" and temp != "latest" and temp != "min" and temp != "oldest":
            try:
                temp = float(temp.replace(" ", ""))
                if p == 'page':
                    temp = max(int(temp), 0)
            except Exception:
                if "max" in p or "min" in p or p == "page":
                    continue
                temp = temp

            if ("order" in p.lower() and val.lower() != "desc" and val.lower() != "asc") or ("sort" in p.lower() and val.lower() != "blocktime" and val.lower() != "amount" and val.lower() != "usdAmount"):
                continue

            params[p] = temp
    
    return params

def getGraphData(request, coin=None):    
    return JsonResponse(coinController.getGraphData(getParams(request), request.GET.get("lastId") or 0), safe=False)
