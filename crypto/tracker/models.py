from django.db import models
from django.http import Http404
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AnonymousUser as DjangoAnonymousUser
from coin.models import Coin
import json
import os
import sys

class Settings(models.Model):
    user     = models.OneToOneField(User, on_delete=models.CASCADE)

    darkMode = models.BooleanField(default=False)
    premium  = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Settings.objects.create(user=instance)
        instance.addCoin("USDT")
    instance.settings.save()

class AnonymousUser(DjangoAnonymousUser):
    def __init__(self, request):
        super(AnonymousUser, self).__init__()
    
    def getCoin(self, coin):
        try:
            return Coin.objects.filter(name__iexact=coin).first()
        except Exception as e:
            raise Http404("Invalid Coin") 

def getCoin(self, coin):
    try:
        return self.coins.all().get(name__iexact=coin)
    except Coin.DoesNotExist as e:
        raise Http404("Invalid Coin") 

def addCoin(self, coin):
    try:
        self.getCoin(coin)
    except Http404 as e:
        self.coins.create(name=coin, user=self)
        
User.add_to_class('getCoin', getCoin)
User.add_to_class('addCoin', addCoin)
"""
class JSONField(models.TextField):
    def to_python(self, value):
        if value == "":
            return None

        try:
            if isinstance(value, str):
                return json.loads(value)
        except ValueError:
            pass
        return value

    def from_db_value(self, value, *args):
        return self.to_python(value)

    def get_db_prep_save(self, value, *args, **kwargs):
        if value == "":
            return None
        if isinstance(value, dict):
            value = json.dumps(value, cls=DjangoJSONEncoder)
        return value

class Profile(models.Model):
    user     = models.OneToOneField(User, on_delete=models.CASCADE)
    sessions = JSONField(blank=False, default=r"{'usdt': {}, 'btc': {}}")

    def getSession(self, coin, session=""):
        coin = coin.lower()

        self.sessions = json.loads(str(self.sessions).replace("'", '"'))

        if coin != "usdt":
            return None

        if session in self.sessions[coin]:
            return self.sessions[coin][session]
        
        return json.load(open(path + coin + ".json"))

    def addAddr(self, reqData, coin, filters):
        node = {
                "name": reqData.get("name", ""),
                "addr": reqData.get("addr", ""),
                "url": "/{}/search/{}?".format(coin, reqData.get("addr", ""))
            }
        cat = reqData.get("cat", "")

        if isValidName(node['name']) and isValidAddr(node['addr']) and self.uniqName(node['name']) and isValidName(cat):
            session = self.getSession(coin, reqData.get("session", ""))

            if cat in session:
                session[cat]['url'] += "&addr[]={}".format(node['addr'])
                session[cat]['addrs'].append(node)
            else:
                session[cat] = {
                    'url': "/{}/search/{}?addr[]={}&minTx={}".format(self.coin, cat, node['addr'], 1000000),#DMinTx()),
                    'addrs': [node]
                }
                
            return "Success"
        
        return "ERROR"

    def uniqName(self, name, addr):
        addrs = self.getKnownList()[0]['addrs']
        
        for node in addrs:
            if node['name'].lower() == name.lower() and node['addr'] != addr:
                return False

        return True

    def delAddr(self, reqData, coin): 
        session = self.getSession(coin, reqData.get("session", ""))

        for cat, info in session.items():
            for i in range(len(info['addrs'])):
                if session[cat]['addrs'][i]['addr'] == reqData.get("addr", ""):
                    del session[cat]['addrs'][i]
                    return "Success"
            
        return "ERROR"

    def editAddr(self, reqData, filters):
        addr = reqData.get("addr", "")
        name = reqData.get("name", "")
        cat  = reqData.get("cat", "")

        if isValidAddr(addr) and isValidName(name) and not self.nameExists(name, addr=addr) and self.isValidName(cat):
            if self.delAddr(addr) == "Success" and self.addAddr(addr, name, cat, filters) == "Success":
                return "Success"
            
        return "ERROR"

    def popCat(self, cat, coin, session):
        if self.getSession(coin, session):
            return self.sessions[coin][session].pop(cat)

        return None

    def delCat(self, reqData, coin):
        if self.popCat(reqData.get("cat", ""), coin, reqData.get("session", "")):
            return "Success"
        
        return "ERROR"

    def editCat(self, reqData, coin, filters):
        prevCat = reqData.get("prevCat", "")
        newCat  = reqData.get("newCat", "")

        if isValidName(prevCat) and isValidName(newCat):  
            session = self.getSession(coin, reqData.get("session", ""))

            if session and prevCat in session:
                session[newCat] = session.pop(prevCat)
                session[newCat]['url'] = "/{}/search/{}?".format(coin, newCat)
                
                for addr in session[newCat]['addrs']:
                    session[newCat]['url'] += "&addr[]=" + addr['addr']

                session[newCat]['url'] = addFilters(session[newCat]['url'], filters=filters)

                print(session)

                return "Success"

        return "ERROR"

    def getKnown(self, addr, coin, session):
        for known in self.getKnownList(coin, session)[0]['addrs']:
            if known['addr'] == addr:
                return known
        
        return {"name": addr, "addr": addr, "url": addr}#self.urls['addr'] + addr}

    def getKnownList(self, coin, session):
        catDict = self.getSession(coin, session)

        catList    = []

        for cat, info in catDict.items():
            if cat == "Home":
                continue

            for addr in info['addrs']:
                if "Home" not in catDict:
                    catDict['Home'] = {
                        'url': "/{}/search/Home?addr[]={}".format(coin, addr['addr']),
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

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
"""