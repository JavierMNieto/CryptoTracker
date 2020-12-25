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
    
    def get_coin(self, coin):
        try:
            return Coin.objects.filter(name__iexact=coin).first()
        except Exception as e:
            raise Http404("Invalid Coin") 

def get_coin(self, coin):
    try:
        return self.coins.all().get(name__iexact=coin)
    except Coin.DoesNotExist as e:
        raise Http404("Invalid Coin") 

def add_coin(self, coin):
    try:
        self.get_coin(coin)
    except Http404 as e:
        self.coins.create(name=coin, user=self)
        
User.add_to_class('get_coin', get_coin)
User.add_to_class('add_coin', add_coin)
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

    def addAddr(self, req_data, coin, filters):
        node = {
                "name": req_data.get("name", ""),
                "addr": req_data.get("addr", ""),
                "url": "/{}/search/{}?".format(coin, req_data.get("addr", ""))
            }
        cat = req_data.get("cat", "")

        if is_valid_name(node['name']) and is_valid_addr(node['addr']) and self.uniqName(node['name']) and is_valid_name(cat):
            session = self.getSession(coin, req_data.get("session", ""))

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
        addrs = self.get_knownList()[0]['addrs']
        
        for node in addrs:
            if node['name'].lower() == name.lower() and node['addr'] != addr:
                return False

        return True

    def delAddr(self, req_data, coin): 
        session = self.getSession(coin, req_data.get("session", ""))

        for cat, info in session.items():
            for i in range(len(info['addrs'])):
                if session[cat]['addrs'][i]['addr'] == req_data.get("addr", ""):
                    del session[cat]['addrs'][i]
                    return "Success"
            
        return "ERROR"

    def editAddr(self, req_data, filters):
        addr = req_data.get("addr", "")
        name = req_data.get("name", "")
        cat  = req_data.get("cat", "")

        if is_valid_addr(addr) and is_valid_name(name) and not self.nameExists(name, addr=addr) and self.is_valid_name(cat):
            if self.delAddr(addr) == "Success" and self.addAddr(addr, name, cat, filters) == "Success":
                return "Success"
            
        return "ERROR"

    def popCat(self, cat, coin, session):
        if self.getSession(coin, session):
            return self.sessions[coin][session].pop(cat)

        return None

    def delCat(self, req_data, coin):
        if self.popCat(req_data.get("cat", ""), coin, req_data.get("session", "")):
            return "Success"
        
        return "ERROR"

    def edit_cat(self, req_data, coin, filters):
        prevCat = req_data.get("prevCat", "")
        newCat  = req_data.get("newCat", "")

        if is_valid_name(prevCat) and is_valid_name(newCat):  
            session = self.getSession(coin, req_data.get("session", ""))

            if session and prevCat in session:
                session[newCat] = session.pop(prevCat)
                session[newCat]['url'] = "/{}/search/{}?".format(coin, newCat)
                
                for addr in session[newCat]['addrs']:
                    session[newCat]['url'] += "&addr[]=" + addr['addr']

                session[newCat]['url'] = addFilters(session[newCat]['url'], filters=filters)

                print(session)

                return "Success"

        return "ERROR"

    def get_known(self, addr, coin, session):
        for known in self.get_knownList(coin, session)[0]['addrs']:
            if known['addr'] == addr:
                return known
        
        return {"name": addr, "addr": addr, "url": addr}#self.urls['addr'] + addr}

    def get_knownList(self, coin, session):
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