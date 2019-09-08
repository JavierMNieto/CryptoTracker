from django.http import HttpResponse
from django.template import loader
from neo4j.v1 import GraphDatabase
#from btc.models import Node as btcNode
#from usdt.models import Node as usdtNode
from django.shortcuts import render
import ccxt
import json
import time
import math
import requests
import sys

sys.path.append("../")
from coin.query import formatFilters
from coin.defaults import DParams

def numWithCommas(num):
	return ("{:,}".format(float(num)))

def search(request, coin=None):
	if coin is None:
		coin = 'usdt'
	cmc = ccxt.coinmarketcap()
	btc = cmc.fetch_ticker('BTC/USD')

	filters = formatFilters(DParams())

	search = {'coin': coin, 'homeUrl': '/{}/search/0'.format(coin), 'btc': btc, 'dFilters': json.dumps(filters)}
	return render(request, 'tracker/index.html', search)

def usdt_home(request):
	return search(request, 'usdt')

def btc_home(request):
	return search(request, 'btc')

def home(request):
	cmc = ccxt.coinmarketcap()
	btc = cmc.fetch_ticker('BTC/USD')
	return render(request, 'tracker/index.html', {'search': [], 'coin': 'home', 'homeUrl': '#', 'btc': btc})