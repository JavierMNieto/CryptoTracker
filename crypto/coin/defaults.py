"""
    Default minimum transaction amount (USD)
"""
def DMinTx():
    return 1000000 # 1 Mil

"""
    Default query parameters when getting info from neo4j
"""
def DParams():
    return {
        'addr[]': None,
        'sender[]': None,
        'receiver[]': None,
        'sort': 'epoch',
        'order': 'DESC',
        'page': 0,
        'minBal': -1,
        'maxBal': 1e16, 
        'minTx': DMinTx(), 
        'maxTx': 1e16, 
        'minTime': -1, 
        'maxTime': 1e16,
        'minTotal': -1, 
        'maxTotal': 1e16, 
        'minTxsNum': -1, 
        'maxTxsNum': 1e16, 
        'minAvg': -1, 
        'maxAvg': 1e16
    }

"""
    URLs of info on coins (img, explorer, etc.)
"""
def Urls():
    return {
        'BTC': {
            'tx': 'https://blockexplorer.com/tx/',
            'addr': 'https://blockexplorer.com/address/',
            'img': '/static/images/btc.png'
        },
        'USDT': {
            'tx': 'https://omniexplorer.info/tx/',
            'addr': '/usdt/search/',
            'img': '/static/images/usdt.png'
        }
    }

"""
    Number of transactions per page
"""
def TxsPerPage():
    return 10

"""
    Definition of satoshi in which many cryptocurrencies are stored in
"""
def Satoshi():
    return 100000000.0

"""
    Neo4j graph database credentials
"""
def Neo4j(): 
    return {
        'user': 'neo4j',
        'pass': '2282002',
        'url': 'bolt://localhost:7687'
    }