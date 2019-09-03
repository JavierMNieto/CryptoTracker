from .defaults import *
from neo4j import GraphDatabase
import json
import time
import re
import os

def numWithCommas(num):
    return ("{:,}".format(float(num)))

class CoinController:

    def __init__(self):
        self.driver = GraphDatabase.driver(Neo4j()['url'], auth=(Neo4j()['user'], Neo4j()['pass']))
        self.coin   = 'USDT'
        self.urls   = []

        # TEMPORARY
        self.path   = os.path.dirname(os.path.realpath(__file__)) + "/"
        
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
        query = (TxsQuery() + "RETURN r ORDER BY r." + params['sort'] + " " + params['order'] + " SKIP " + str(int(params['page']*TxsPerPage())) + " LIMIT " + str(TxsPerPage()))

        addrsText = ''
        
        print(params)

        if params['addr[]']:
            addrsText = "({}) AND".format(self.getAddrsText(params['addr[]']))

            query     = "MATCH (a:{})-[r:{}TX]->(b:{}) WHERE {} {}".format(self.coin, self.coin, self.coin, addrsText, query)
        elif params['sender[]'] and params['receiver[]']:
            addrsText = "({}) AND".format(self.getAddrsText(params['sender[]'], params['receiver[]'], rel=False))

            query     = "MATCH (a:{})-[r:{}TX]->(b:{}) WHERE {} {}".format(self.coin, self.coin, self.coin, addrsText, query.replace("WITH startNode(r) as a, endNode(r) as b, r ", ""))
        else:
            query = "MATCH (a:{})-[r:{}TX]->(b:{}) WHERE {}".format(self.coin, self.coin, self.coin, query)

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
                "source": self.getKnown(aNode['addr'])['name'],
                "sourceAddr": aNode['addr'],
                "target": self.getKnown(bNode['addr'])['name'],
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

    def getAddrInfo(self, addr, filters):

        info = {
            "label": "",
            "addr": None,
            "totalTxs": 0,
            "lastTx": 1230940800, #REMOVE
            "balance": 0,
            "filters": {}
        }

        if addr == "0":
            info["label"]    = "All Addresses"
        elif filters['addr[]']:
            info['label']    = addr

            if len(addr) < 2:
                info['label'] = "Custom Graph"          

            info['addr']     = filters['addr[]']
            
            info['balance']  = self.driver.session().run("MATCH (a: " + self.coin + ") WHERE " + self.getAddrsText(info['addr'], rel=False) + " RETURN SUM(a.balance)").single().value()
        else:
            node = self.driver.session().run("MATCH (a:" + self.coin + ") WHERE a.addr = {addr} RETURN a", addr=addr).single()
            
            if node:
                node = node.value()
            else:
                info['address'] = addr + " DOES NOT EXIST"
                return {"search": info}

            info['label']   = self.getKnown(node['addr'])['name']

            info['addr']    = [node['addr']]
            info['balance'] = node['balance']
            info['address'] = node['addr'] # CHANGE - CONFUSING   
        
        # WHAT WERE YOU THINKING?
        if 'address' in info:
            info['url'] = self.urls['addr'] + info['address']

        addrText = ""

        if info['addr']:
            addrText = self.getAddrsText(info['addr']) + " AND "

        query  = "MATCH (a:{})-[r:{}TX]->(b:{}) WHERE {} {} RETURN count(r)".format(self.coin, self.coin, self.coin, addrText, TxsQuery())

        info["totalTxs"] = self.runFilters(query, filters).single().value()
        
        for f, val in filters.items():
            if "min" in f or "max" in f:
                info['filters'][f] = val

        return {
            "search": info
        }
    
    def getGraphData(self, params):
        query = GraphQuery()
        
        addrsText = ''

        data = {
            'nodes': [],
            'edges': [],
            'totalTxs': 0
        }

        if params['addr[]']:
            """
            for addr in params['addr[]']:
                if not self.isValidAddr(addr):
                    return data
            """

            addrsText = "({}) AND".format(self.getAddrsText(params['addr[]']))


        query = "MATCH (a:{})-[r:{}TX]->(b:{}) WHERE {} {}".format(self.coin, self.coin, self.coin, addrsText, query)
        
        txs   = self.runFilters(query, params)
        
        id = 0
        for nodes in txs:
            nodes = nodes.get('result')
            if nodes is None:
                continue
            aNode = nodes['from']
            aKnown = self.getKnown(aNode['addr'])
            aNode = {
                "id": aNode.id,
                "label": aKnown['name'],
                "addr": aNode['addr'],
                "balance": float(aNode['balance'] or 0),
                "balVal": float(aNode['balance'] or 0),
                "group": aNode['wallet'] or 'usdt',
                "lastUpdate": aNode['epoch'] or time.time(),
                "url": aKnown['url'],
                "webUrl": self.urls['addr'] + aNode['addr'], # REMOVE
                "value": float(aNode['balance'] or 0)/Satoshi(),
                "img": self.urls['img'],
                "title": ("Address: {}<br> "
                        "Balance: ${}<br> ").format(aNode['addr'], numWithCommas(float(aNode['balance'] or "0")))
            }
            if aNode['label'] != aNode['addr']:
                aNode['title'] = "Name: {}<br>".format(aNode['label']) + aNode['title']
                
            bNode  = nodes['to']
            bKnown = self.getKnown(bNode['addr'])
            bNode = {
                "id": bNode.id,
                "label": bKnown['name'],
                "addr": bNode['addr'],
                "balance": float(bNode['balance'] or 0),
                "balVal": float(bNode['balance'] or 0),
                "group": bNode['wallet'] or 'usdt',
                "lastUpdate": bNode['epoch'] or time.time(),
                "url": bKnown['url'],
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
                "sourceAddr": aNode['addr'],
                "targetAddr": bNode['addr'],
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

    def getKnown(self, addr):
        for known in self.getKnownList()[0]['addrs']:
            if known['addr'] == addr:
                return known
        
        return {"name": addr, "addr": addr, "url": self.urls['addr'] + addr}
    
    def getKnownDict(self):
        return json.load(open(self.path + self.coin + ".json"))

    def getKnownList(self):
        catDict = self.getKnownDict()

        catList    = []

        for cat, info in catDict.items():
            if cat == "Home":
                continue

            for addr in info['addrs']:
                if "Home" not in catDict:
                    catDict['Home'] = {
                        'url': "/{}/search/Home?addr[]={}".format(self.coin, addr['addr']),
                        'addrs': []
                    }
                else:
                    catDict['Home']['url'] += "&addr[]={}".format(addr['addr'])

            catDict['Home']['addrs'] += info['addrs']

            catList.append({
                'category': cat,
                'url': info['url'],
                'addrs': info['addrs']
            })

        if "Home" not in catDict:
            catList.append({
                'category': 'Home',
                'url': "",
                'addrs': []
            })
        else:
            catList.insert(0, {
                'category': 'Home',
                'url': catDict['Home']['url'],
                'addrs': catDict['Home']['addrs']
            })

        return catList
    
    def addAddr(self, addr, name, cat):
        try: 
            if self.isValidName(name) and self.isValidAddr(addr) and not self.nameExists(name) and self.isValidName(cat):
                catDict = self.getKnownDict()
                with open(self.path + self.coin + ".json", "w") as f:
                    node = {
                            "name": name,
                            "addr": addr,
                            "url": "/{}/search/{}".format(self.coin, addr)
                        }

                    if cat in catDict:
                        catDict[cat]['url'] += "&addr[]={}".format(addr)
                        catDict[cat]['addrs'].append(node)
                    else:
                        catDict[cat] = {
                            'url': "/{}/search/Home?addr[]={}".format(self.coin, addr),
                            'addrs': [node]
                        }

                    json.dump(catDict, f)

                    return "Success"
        except Exception as e:
            print(e)

        return "ERROR"
        
    def getAddrsText(self, addr, extras=[], rel=True):
        addrsText = ""
        for x in range(len(addr)):
            string = ""

            string += "a.addr = '{}'".format(addr[x])
            if rel:
                string = "({} or b.addr = '{}')".format(string, addr[x])
            

            if x < len(extras):
                string = "({} AND b.addr = '{}')".format(string, extras[x])

            if addrsText != "":
                string = " OR " + string

            addrsText += string

        return "({})".format(addrsText)

    def delAddr(self, addr): 
        try: 
            if self.isValidAddr(addr):
                catDict = self.getKnownDict()
                with open(self.path + self.coin + ".json", "w") as f:
                    for cat, info in catDict.items():
                        for i in range(len(info['addrs'])):
                            if catDict[cat]['addrs'][i] == addr:
                                del catDict[cat]['addrs'][i]
                                json.dump(catDict, f)
                                return "Success"
        except Exception as e:
            print(e)
            
        return "ERROR"

    def isValidName(self, name):            
        return len(name) < 16 and len(name) > 2 and re.match(r'^[A-Za-z0-9_-]*$', name) != None

    def nameExists(self, name):
        addrs = self.getKnownList()[0]['addrs']
        
        for addr in addrs:
            if addr['name'].lower() == name.lower():
                return True
 
        return False

    def isValidAddr(self, addr):
        if len(addr) == 34 and ' ' not in addr and re.match(r'^[A-Za-z0-9]*$', addr):
            node = self.driver.session().run("MATCH (a:" + self.coin + ") WHERE a.addr = '" + addr + "' RETURN a").single()

            if node:
                return True
        return False

    def editCat(self, prevCat, newCat):
        try:
            if self.isValidName(prevCat) and self.isValidName(newCat) and prevCat.lower() != "home":
                catDict = self.getKnownDict()  
                if prevCat in catDict:
                    with open(self.path + self.coin + ".json", "w") as f:
                        catDict[newCat] = catDict.pop(prevCat)
                        json.dump(catDict, f)
                        return "Success"
        except Exception as e:
            print(e)

        return "ERROR"

    def editAddr(self, addr, name, cat):
        try: 
            if self.isValidAddr(addr) and self.isValidName(name) and not self.nameExists(name) and self.isValidName(cat):
                if self.delAddr(addr) == "Success" and self.addAddr(addr, name, cat) == "Success":
                    return "Success"
        except Exception as e:
            print(e)
            
        return "ERROR"
