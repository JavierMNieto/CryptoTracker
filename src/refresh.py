from search import Search
from constants import neo4j, timeout
from twisted.internet import task, reactor

search = Search('https://blockchain.info/rawaddr/', 'https://api.omniwallet.org/v1/address/addr/details/', {'url': 'bolt://localhost:7687', 'user': neo4j['user'], 'pass': neo4j['pass']})

def refresh():
	search.refresh()
	search.collapse()

refreshInterval = task.LoopingCall(refresh)
refreshInterval.start(timeout)

reactor.run()