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

def addr(request, coin=None):
    if request.method == "GET":
        if request.GET.get('method') == "isValid":
            return JsonResponse(coinController.isValidAddr(request.GET.get('addr')), safe=False)

    if request.method != "POST":
        return

    coinController.setCoin(coin)
    
    method = request.POST.get('method') or ""

    if method == "add":
        return JsonResponse(coinController.addAddr(request.POST.get('addr'), request.POST.get('name')), safe=False)
    elif method == "edit":
        return JsonResponse(coinController.editAddr(request.POST.get('addr'), request.POST.get('name')), safe=False)
    elif method == "delete":
        return JsonResponse(coinController.delAddr(request.POST.get('addr')), safe=False)
    else:
        return

def search(request, id, coin=None):
    if 'img' in str(id) and '{' in str(id):
        return render(request, 'coin/coin.html')
    
    coinController.setCoin(coin)

    id = unquote(id)
    
    data = coinController.getAddrInfo(id)

    return render(request, 'coin/coin.html', data)

def getParams(request):
    coinController.setCoin(request.build_absolute_uri())
    
    params = DParams()
    for p, val in params.items():
        temp = None
        
        if '[]' in p:
            temp = request.GET.getlist(p)
        else:
            temp = request.GET.get(p)
        
        if temp:
            try:
                temp = float(temp.replace(" ", ""))
                if p == 'page':
                    temp = max(temp, 0)
            except Exception:
                temp = temp
            
            params[p] = temp
            
    return params

def getGraphData(request, coin=None):    
    return JsonResponse(coinController.getGraphData(getParams(request)), safe=False)
