from django.http import HttpResponse
from django.template import loader
from neo4j.v1 import GraphDatabase
from . import constants
from btc.models import Node as btcNode
from usdt.models import Node as usdtNode
from django.shortcuts import render
import ccxt
import json

driver = GraphDatabase.driver(constants.neo4j['url'], auth=(constants.neo4j['user'], constants.neo4j['pass']))
models = {
	'btc': btcNode,
	'usdt': usdtNode
}

def search(request, coin=None):
	if coin is None:
		coin = 'usdt'
	cmc = ccxt.coinmarketcap()
	btc = cmc.fetch_ticker('BTC/USD')

	nodes = models[coin].objects.order_by('name')

	categories = [{
		'category': 'Home',
		'url': "/{}/search/0".format(coin),
		'addrs': []
	}]
	for node in nodes:
		categories[0]['addrs'].append({
			'addr': node.name,
			'url': "/{}/search/{}".format(coin, node.name)
		})
		if node.category == '':
			continue
		add = True
		for category in categories:
			if category['category'] == node.category:
				category['addrs'].append({
					'addr': node.name,
					'url': "/{}/search/{}".format(coin, node.name)
				})
				category['url'].append(node.name)
				add = False
				break
		if add:
			categories.append({
				'category': node.category,
				'url': [node.name],
				'addrs': [{
					'addr': node.name,
					'url': "/{}/search/{}".format(coin, node.name)
				}]
			})
	for category in categories:
		if category['category'] == 'Home':
			continue
		category['url'] = "/{}/search/{}".format(coin, json.dumps(category['url']))
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