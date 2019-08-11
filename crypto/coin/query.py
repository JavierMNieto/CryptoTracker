from .defaults import *
from neo4j import GraphDatabase
import json
import time
import re

def numWithCommas(num):
    return ("{:,}".format(float(num)))

class CoinController:

    def __init__(self):
        self.driver = GraphDatabase.driver(Neo4j()['url'], auth=(Neo4j()['user'], Neo4j()['pass']))
        self.coin   = ''
        self.urls   = []
        
    def setCoin(self, url):
        if 'btc' in url:
            self.coin = 'BTC'
        else:
            self.coin = 'USDT'
        self.urls = Urls()[self.coin]
    
    def runFilters(self, query, filters=DParams()):
        return self.driver.session().run(query, minBal=filters['minBal'], maxBal=filters['maxBal'], minTx=filters['minTx'], maxTx=filters['maxTx'],
                                        minTime=filters['minTime'], maxTime=filters['maxTime'], minTotal=filters['minTotal'], maxTotal=filters['maxTotal'],
                                        minTxsNum=filters['minTxsNum'], maxTxsNum=filters['maxTxsNum'], minAvg=filters['minAvg'], maxAvg=filters['maxAvg'])

    def getTxs(self, params=DParams()):
        query = ("a.balance > {minBal} AND a.balance < {maxBal} AND b.balance > {minBal} AND b.balance < {maxBal} AND r.usdAmount > {minTx} AND r.usdAmount < {maxTx} AND r.epoch > {minTime} AND r.epoch < {maxTime} "
                    "WITH startNode(r) as a, endNode(r) as b, r "
                    "WITH {id: ID(a), label: a.name, addr: a.addr} AS a, {id: ID(b), label: b.name, addr: b.addr} AS b, {amount: SUM(r.usdAmount),txsNum: count(r),avgTxAmt: SUM(r.usdAmount)/count(r)} as r, COLLECT(r) as txs "
                    "WITH CASE WHEN r.amount > {minTotal} AND r.amount < {maxTotal} AND r.txsNum > {minTxsNum} AND r.txsNum < {maxTxsNum} AND r.avgTxAmt > {minAvg} AND r.avgTxAmt < {maxAvg} THEN "
                    "REDUCE(vals = [], tx in txs | vals + [{from: a, to: b, txid: tx.txid, amount: tx.usdAmount, epoch: tx.epoch, type: TYPE(tx), id: ID(tx)}]) ELSE NULL END AS result "
                    "UNWIND result as r RETURN r ORDER BY r." + params['sort'] + " " + params['order'] + " SKIP " + str(int(params['page']*TxsPerPage())) + " LIMIT " + str(TxsPerPage()))

        addrsText = ''

        isKnown = True
        
        print(params)

        if params['addr[]']:
            addrsText = "({}) AND".format(self.getAddrsText(params['addr[]']))
            isKnown   = self.getIsKnown(params['addr[]'])
            types     = self.getTypes(isKnown)
            query     = "MATCH (a:{})-[r:{}TX]-(b{}) WHERE {} {}".format(types['a'], self.coin, types['b'], addrsText, query)
        elif params['sender[]'] and params['receiver[]']:
            addrsText = "({}) AND".format(self.getAddrsText(params['sender[]'], params['receiver[]']))
            isKnown   = self.getIsKnown(params['receiver[]']) and self.getIsKnown(params['sender[]'])
            
            types     = self.getTypes(isKnown)
            query     = "MATCH (a:{})-[r:{}TX]->(b{}) WHERE {} {}".format(types['a'], self.coin, types['b'], addrsText, query.replace("WITH startNode(r) as a, endNode(r) as b, r ", ""))
        else:
            types = self.getTypes(isKnown)
            query = "MATCH (a:{})-[r:{}TX]-(b{}) WHERE {}".format(types['a'], self.coin, types['b'], query)

        txs = self.runFilters(query, params)

        edges = []

        for tx in txs:
            rel = tx.get('r')
            aNode = rel['from']
            bNode = rel['to']

            rel = {
                "from": aNode['id'],
                "to": bNode['id'],
                #"id": rel['id'],
                "value": float(rel['amount']),
                "source": aNode['label'],
                "sourceAddr": aNode['addr'],
                "target": bNode['label'],
                "targetAddr": bNode['addr'],
                "type": rel['type'],
                "amount": float(rel['amount']),
                "time": rel['epoch'],
                "txid": rel['txid'],
                "img": self.urls['img'],
                "txidUrl": self.urls['tx'] + rel['txid'],
                "sourceUrl": self.urls['addr'] + aNode['addr'],
                "targetUrl": self.urls['addr'] + bNode['addr']
            }
            edges.append(rel)

        return edges

    # TEMPORARY
    def getIsKnown(self, addrs):
        if addrs is None: 
            return False
        
        for addr in addrs:
            node = self.driver.session().run("MATCH (a:" + self.coin + "KNOWN) WHERE a.addr = {addr} RETURN a", addr=addr).single()
            if node == None:
                return False
        
        return True

    def getTypes(self, isKnown=True):
        types = {
            "a": self.coin,
            "b": ""
        }

        if isKnown:
            types["a"] += "KNOWN"
                    
        return types

    def getAddrInfo(self, addr):     
        types = {}
                    
        info = {
            "label": "",
            "addr": None,
            "totalTxs": 0,
            "minTx": DMinTx(),
            "lastTx": 1230940800,
            "balance": 0
        }
          
        if addr == "0":
            info["label"]    = "All Addresses"
            types = self.getTypes(self.getIsKnown(info['addr']))
        elif "[" in addr:
            addr = json.loads(addr)
            
            addrs = []
            label = ""
            isCategory = False
            for addy in addr:
                if '.' in addy:
                    if label == "":
                        label += addy.split('.', 1)[1]
                        isCategory = True
                    else:
                        label += ", {}".format(addy.split('.', 1)[1])
                    continue
                addrs.append(addy)
                if not isCategory:
                    if label == "":
                        label += addy
                    else:
                        label += ", " + addy            

            info['label']    = label
            info['addr']     = addrs
            
            types = self.getTypes(self.getIsKnown(info['addr']))
    
            info['balance']  = self.driver.session().run("MATCH (a: " + types['a'] + ") WHERE " + self.getAddrsText(addrs) + " RETURN SUM(a.balance)").single().value()
        else:
            types = self.getTypes(self.getIsKnown([addr]))
            
            node = self.driver.session().run("MATCH (a:" + types['a'] + ") WHERE a.addr = {addr} RETURN a", addr=addr).single()
            
            if node:
                node = node.value()
            else:
                info['address'] = addr
                return {"search": info}

            info['label']   = node['name']
            info['addr']    = [node['addr']]
            info['balance'] = node['balance']
            info['address'] = node['addr']
            info['minTx']   = node['minTx'] or info['minTx']     
        
        if 'address' in info:
            info['url'] = self.urls['addr'] + info['address']

        query  = "MATCH (a:{})-[r:{}TX]-(b{}) WHERE a.balance > -1 AND b.balance > -1".format(types['a'], self.coin, types['b'])

        if info['addr']:
            query += " AND ({})".format(self.getAddrsText(info['addr']))

        info["totalTxs"] = self.driver.session().run(query + " AND r.usdAmount > {minTx} RETURN count(r)", minTx=info['minTx']).single().value()
        
        return {
            "search": info
        }
    
    def getGraphData(self, params):
        query = ("a.balance > {minBal} AND a.balance < {maxBal} AND b.balance > {minBal} AND b.balance < {maxBal} AND r.usdAmount > {minTx} "
                  "AND r.usdAmount < {maxTx} AND r.epoch > {minTime} AND r.epoch < {maxTime} WITH DISTINCT startNode(r) as a, endNode(r) as b, {amount: SUM(r.usdAmount),txsNum: count(r),avgTxAmt: SUM(r.usdAmount)/count(r)} AS r "
                  "RETURN CASE WHEN r.amount > {minTotal} AND r.amount < {maxTotal} AND r.txsNum > {minTxsNum} AND r.txsNum < {maxTxsNum} AND r.avgTxAmt > {minAvg} AND r.avgTxAmt < {maxAvg} THEN {from:a, to:b, r:r} ELSE null END AS result") 
        
        addrsText = ''

        isKnown = True

        if params['addr[]']:
            addrsText = "({}) AND".format(self.getAddrsText(params['addr[]']))
            isKnown   = self.getIsKnown(params['addr[]'])

        types = self.getTypes(isKnown)

        query = "MATCH (a:{})-[r:{}TX]-(b{}) WHERE {} {}".format(types['a'], self.coin, types['b'], addrsText, query)
        
        txs   = self.runFilters(query, params)
        
        data = {
            'nodes': [],
            'edges': [],
            'totalTxs': 0
        }
        
        id = 0
        for nodes in txs:
            nodes = nodes.get('result')
            if nodes is None:
                continue
            aNode = nodes['from']
            aNode = {
                "id": aNode.id,
                "label": aNode['name'],
                "addr": aNode['addr'],
                "balance": float(aNode['balance'] or 0),
                "balVal": float(aNode['balance'] or 0),
                "group": aNode['wallet'] or 'usdt',
                "lastUpdate": aNode['epoch'] or time.time(),
                "url": self.urls['addr'] + aNode['addr'],
                "webUrl": self.urls['addr'] + aNode['addr'], # REMOVE
                "value": float(aNode['balance'] or 0)/Satoshi(),
                "img": self.urls['img'],
                "title": ("Address: {}<br> "
                        "Balance: ${}<br> ").format(aNode['addr'], numWithCommas(float(aNode['balance'] or "0")))
            }
            if aNode['label'] != aNode['addr']:
                aNode['title'] = "Name: {}<br>".format(aNode['label']) + aNode['title']
                
            bNode = nodes['to']
            bNode = {
                "id": bNode.id,
                "label": bNode['name'],
                "addr": bNode['addr'],
                "balance": float(bNode['balance'] or 0),
                "balVal": float(bNode['balance'] or 0),
                "group": bNode['wallet'] or 'usdt',
                "lastUpdate": bNode['epoch'] or time.time(),
                "url": self.urls['addr'] + bNode['addr'],
                "webUrl": self.urls['addr'] + bNode['addr'], # REMOVE
                "value": float(bNode['balance'] or 0)/Satoshi(),
                "img": self.urls['img'],
                "title": ("Address: {}<br> "
                        "Balance: ${}<br> ").format(bNode['addr'], numWithCommas(float(bNode['balance'] or "0")))
            }
            if bNode['label'] != bNode['addr']:
                bNode['title'] = "Name: {}<br>".format(bNode['label']) + bNode['title']
                
            rel = nodes['r']
            id += 1
            rel = {
                "from": aNode['id'],
                "to": bNode['id'],
                "id": id,
                "value": float(rel['amount'] or 0),
                "source": aNode['label'],
                "target": bNode['label'],
                "amount": float(rel['amount'] or 0),
                "txsNum": int(rel['txsNum'] or 1.0),
                "avgTx": float(rel['avgTxAmt'] or rel['amount'] or 0),
                "img": self.urls['img'],
                "color": {
                    "color": "#26A17B"
                },
                "sourceUrl": self.urls['addr'] + aNode['addr'],
                "targetUrl": self.urls['addr'] + bNode['addr']
            }
            rel['title'] = ("# of Txs: {}<br> "
                            "Total: ${}<br> "
                            "Average Tx Amount: ${}<br>".format(numWithCommas(rel['txsNum']), numWithCommas(rel['amount']), numWithCommas(rel['avgTx'])))
            data['totalTxs'] += rel['txsNum']
            aExists = False
            bExists = False
            for node in data['nodes']:
                if node['id'] == aNode['id']:
                    aExists = True
                if node['id'] == bNode['id']:
                    bExists = True
                if aExists and bExists:
                    break
            if not aExists:
                data['nodes'].append(aNode)
            if not bExists:
                data['nodes'].append(bNode)
            data['edges'].append(rel)
        
        return data
        
    def addAddr(self, addr, name): 
        if self.isValidName(name) and self.isValidAddr(addr) and not self.nameExists(name):   
            node = self.driver.session().run("MATCH (a:" + self.coin + ") WHERE a.addr = '{addr}' REMOVE a:" + self.coin + " SET a:" + self.coin + "KNOWN, a.name = '{name}' RETURN a", addr=addr, name=name).single()
            
            if node:
                return "Success"
        return "ERROR"
        
    def getAddrsText(self, addr, extras=[]):
        addrsText = ""
        for x in range(len(addr)):
            string = ""

            string += "a.addr = '{}'".format(addr[x])

            if x < len(extras):
                string = "({} AND b.addr = '{}')".format(string, extras[x])

            if addrsText != "":
                string = " OR " + string

            addrsText += string

        return addrsText

    def delAddr(self, addr): 
        if self.isValidAddr(addr, True):
            node = self.driver.session().run("MATCH (a:" + self.coin + "KNOWN) WHERE a.addr = '" + addr + "' REMOVE a:" + self.coin + "KNOWN SET a:" + self.coin + " RETURN a").single()
            
            if node:
                return "Success"
        return "ERROR"

    def isValidName(self, name):            
        return len(name) < 16 and re.match(r'^[A-Za-z0-9_-]*$', name) != None

    def nameExists(self, name):
        node = self.driver.session().run("MATCH (a:" + self.coin + "KNOWN) WHERE a.name = '" + name + "' RETURN a").single()
 
        return node != None

    def isValidAddr(self, addr, known=False):
        if len(addr) == 34 and ' ' not in addr and re.match(r'^[A-Za-z0-9]*$', addr):
            add = ""
            if known:
                add = "KNOWN"
            node = self.driver.session().run("MATCH (a:" + self.coin + add + ") WHERE a.addr = '" + addr + "' RETURN a").single()

            if node:
                return True
        return False

    def editAddr(self, addr, name):
        if self.isValidAddr(addr, True) and self.isValidName(name) and not self.nameExists(name):
            node = self.driver.session().run("MATCH (a:" + self.coin + "KNOWN) WHERE a.addr = '" + addr + "' SET a.name = '" + name + "' RETURN a").single()

            if node:
                return "Success"
        return "ERROR"
