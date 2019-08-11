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

driver = GraphDatabase.driver(constants.neo4j['url'], auth=(constants.neo4j['user'], constants.neo4j['pass']))
dFilters = {'minBal':-1,'maxBal':1e99,'minTx':-1,'maxTx':1e99,'minTime':-1,'maxTime':1e99,'minTotal':-1,'maxTotal':1e99,'minTxsNum':-1,'maxTxsNum':1e99,'minAvg':-1,'maxAvg':1e99}

def numWithCommas(num):
	return ("{:,}".format(float(num)))

def search(request, coin=None):
	if coin is None:
		coin = 'usdt'
	cmc = ccxt.coinmarketcap()
	btc = cmc.fetch_ticker('BTC/USD')

	nodes = driver.session().run("MATCH (a:USDTKNOWN) RETURN a")

	categories = [{
		'category': 'Home',
		'url': "/{}/search/0".format(coin),
		'addrs': []
	}]
	for node in nodes:
		categories[0]['addrs'].append({
			'name': node.get('a')['name'],
			'url': "/{}/search/{}".format(coin, node.get('a')['addr']),
			'addr': node.get('a')['addr']
		})
	search = {'search': categories[0]['addrs'], 'categories': categories, 'coin': coin, 'homeUrl': '/{}/search/0'.format(coin), 'btc': btc}
	return render(request, 'tracker/index.html', search)

def usdt_home(request):
	return search(request, 'usdt')

def btc_home(request):
	return search(request, 'btc')

def home(request):
	cmc = ccxt.coinmarketcap()
	btc = cmc.fetch_ticker('BTC/USD')
	return render(request, 'tracker/index.html', {'search': [], 'coin': 'home', 'homeUrl': '#', 'btc': btc})