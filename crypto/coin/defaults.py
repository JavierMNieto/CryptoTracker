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
        'minTime': 1230940800, 
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

"""
    Defualt query to get single transactions
"""
def TxsQuery():
    return (" a.balance >= {minBal} AND a.balance <= {maxBal} AND b.balance >= {minBal} AND b.balance <= {maxBal} AND r.amount >= {minTx} AND r.amount <= {maxTx} AND r.epoch >= {minTime} AND r.epoch <= {maxTime} "
            "WITH a, b, r "
            "WITH {id: ID(a), addr: a.addr} AS a, {id: ID(b), addr: b.addr} AS b, {amount: SUM(r.amount),txsNum: count(r),avgTxAmt: SUM(r.amount)/count(r)} as r, COLLECT(r) as txs "
            "WITH CASE WHEN r.amount >= {minTotal} AND r.amount <= {maxTotal} AND r.txsNum >= {minTxsNum} AND r.txsNum <= {maxTxsNum} AND r.avgTxAmt >= {minAvg} AND r.avgTxAmt <= {maxAvg} THEN "
            "REDUCE(vals = [], tx in txs | vals + [{from: a, to: b, txid: tx.txid, amount: tx.amount, epoch: tx.epoch, type: TYPE(tx), id: ID(tx)}]) ELSE NULL END AS result "
            "UNWIND result as r ")

"""
    Defualt query to get graph transactions
"""
def GraphQuery():
    return  (" a.balance >= {minBal} AND a.balance <= {maxBal} AND b.balance >= {minBal} AND b.balance <= {maxBal} AND r.amount >= {minTx} "
                  "AND r.amount <= {maxTx} AND r.epoch >= {minTime} AND r.epoch <= {maxTime} WITH a, b, {amount: SUM(r.amount),txsNum: count(r),avgTxAmt: SUM(r.amount)/count(r)} AS r "
                  "RETURN CASE WHEN r.amount >= {minTotal} AND r.amount <= {maxTotal} AND r.txsNum >= {minTxsNum} AND r.txsNum <= {maxTxsNum} AND r.avgTxAmt >= {minAvg} AND r.avgTxAmt <= {maxAvg} THEN {from:a, to:b, r:r} ELSE null END AS result ") 