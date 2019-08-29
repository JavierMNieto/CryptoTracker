from django.http import HttpResponse
from django.template import loader
from neo4j.v1 import GraphDatabase
from django.http import JsonResponse
from . import constants
#from btc.models import Node as btcNode
#from usdt.models import Node as usdtNode
from django.shortcuts import render
import ccxt
import json
import time
import math
import requests

def numWithCommas(num):
	return ("{:,}".format(float(num)))

def search(request, coin=None):
	if coin is None:
		coin = 'usdt'
	cmc = ccxt.coinmarketcap()
	btc = cmc.fetch_ticker('BTC/USD')

	search = {'coin': coin, 'homeUrl': '/{}/search/0'.format(coin), 'btc': btc}
	return render(request, 'tracker/index.html', search)

def usdt_home(request):
	return search(request, 'usdt')

def btc_home(request):
	return search(request, 'btc')

def home(request):
	cmc = ccxt.coinmarketcap()
	btc = cmc.fetch_ticker('BTC/USD')
	return render(request, 'tracker/index.html', {'search': [], 'coin': 'home', 'homeUrl': '#', 'btc': btc})