from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.core.exceptions import ValidationError
from django.http import Http404
from django.core.validators import MaxLengthValidator, MinLengthValidator, RegexValidator, BaseValidator
from .query import CoinController
import urllib.parse
import time
import sys
import uuid

sys.path.append("../")
from static.py.clean import Filters

addrRegex = r'^[A-Za-z0-9]*$'
nameRegex = r'^[A-Za-z0-9_ -]*$'

def validate_addr(value):
    coin = "USDT" # FIX
    node = CoinController().driver.session().run("MATCH (a:" + coin + ") WHERE a.addr = '" + value + "' RETURN a").single()

    if not node:
        raise ValidationError('{} is not a valid {} address'.format(value, coin))

def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

class FiltersModel(Filters):
    def __init__(self, model):
        filters = {}
        for n, val in model_to_dict(model).items():
            if "min" in n or "max" in n:
                filters[n] = val

        super().__init__(filters)

class Node(models.Model):
    name = models.CharField(max_length=16, validators=[MinLengthValidator(3), RegexValidator(nameRegex)])
    addr = models.CharField(max_length=34, validators=[MinLengthValidator(34), RegexValidator(addrRegex), validate_addr])

    group = models.ForeignKey('Group', related_name='nodes', on_delete=models.CASCADE)

    minBal = models.FloatField(default=Filters.dFilters['minBal'])
    maxBal = models.FloatField(default=Filters.dFilters['maxBal'])
    minTx = models.FloatField(default=Filters.dFilters['minTx'])
    maxTx = models.FloatField(default=Filters.dFilters['maxTx'])
    minTime = models.IntegerField(default=Filters.dFilters['minTime'])
    maxTime = models.IntegerField(default=Filters.dFilters['maxTime'])
    minTotal = models.FloatField(default=Filters.dFilters['minTotal'])
    maxTotal = models.FloatField(default=Filters.dFilters['maxTotal'])
    minTxsNum = models.FloatField(default=Filters.dFilters['minTxsNum'])
    maxTxsNum = models.FloatField(default=Filters.dFilters['maxTxsNum'])
    minAvg = models.FloatField(default=Filters.dFilters['minAvg'])
    maxAvg = models.FloatField(default=Filters.dFilters['maxAvg'])

    def getUrl(self):
        url = self.group.session.getUrl() + "/addr/" + self.addr

        return url + "?" + urllib.parse.urlencode(FiltersModel(self).getChangedFilters()) #FIX

    def setFilters(self, filters):
        self.minBal=filters['minBal']
        self.maxBal=filters['maxBal']
        self.minTx=filters['minTx']
        self.maxTx=filters['maxTx']
        self.minTime=filters['minTime']
        self.maxTime=filters['maxTime']
        self.minTotal=filters['minTotal']
        self.maxTotal=filters['maxTotal']
        self.minTxsNum=filters['minTxsNum']
        self.maxTxsNum=filters['maxTxsNum']
        self.minAvg=filters['minAvg']
        self.maxAvg=filters['maxAvg']
        self.save()

    def getFilters(self):
        return FiltersModel(self).filters

    def getAsDict(self):
        return {
            "name": self.name,
            "addr": self.addr,
            "url": self.getUrl(),
            "filters": FiltersModel(self).getChangedFilters()
        }

    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=16, validators=[MinLengthValidator(3), RegexValidator(nameRegex)])
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey('Session', related_name='groups', on_delete=models.CASCADE)

    minBal = models.FloatField(default=Filters.dFilters['minBal'])
    maxBal = models.FloatField(default=Filters.dFilters['maxBal'])
    minTx = models.FloatField(default=Filters.dFilters['minTx'])
    maxTx = models.FloatField(default=Filters.dFilters['maxTx'])
    minTime = models.IntegerField(default=Filters.dFilters['minTime'])
    maxTime = models.IntegerField(default=Filters.dFilters['maxTime'])
    minTotal = models.FloatField(default=Filters.dFilters['minTotal'])
    maxTotal = models.FloatField(default=Filters.dFilters['maxTotal'])
    minTxsNum = models.FloatField(default=Filters.dFilters['minTxsNum'])
    maxTxsNum = models.FloatField(default=Filters.dFilters['maxTxsNum'])
    minAvg = models.FloatField(default=Filters.dFilters['minAvg'])
    maxAvg = models.FloatField(default=Filters.dFilters['maxAvg'])

    def getUrl(self):        
        url = self.session.getUrl() + "/group/" + str(self.uuid)

        return url + "?" +  urllib.parse.urlencode(FiltersModel(self).getChangedFilters()) #FIX

    def getAddrs(self):
        if self.name == "Home":
            return self.session.getAddrs()

        addrs = []

        for n in self.nodes.all():
            addrs.append(n.addr)
        
        return addrs

    def getNode(self, addr):
        try:
            return self.nodes.all().get(addr=addr)
        except Node.DoesNotExist as e:
            raise Http404("Invalid Address")

    def delNode(self, addr):
        if self.session.uuid != Coin.objects.filter(name__iexact=self.session.coin.name).first().sessions.first().uuid:
            node = self.getNode(addr)

            if node:
                node.delete()
                return "Success"
        
        return "ERROR"

    def setName(self, name):
        if self.session.name != Coin.objects.filter(name__iexact=self.session.coin.name).first().sessions.first().uuid:
            if self.name == "Home":
                raise ValidationError('cannot edit Home')
            self.session.isUniqGroupName(name) # change
            self.name = name
            self.save()
    
    def setFilters(self, filters):
        self.minBal=filters['minBal']
        self.maxBal=filters['maxBal']
        self.minTx=filters['minTx']
        self.maxTx=filters['maxTx']
        self.minTime=filters['minTime']
        self.maxTime=filters['maxTime']
        self.minTotal=filters['minTotal']
        self.maxTotal=filters['maxTotal']
        self.minTxsNum=filters['minTxsNum']
        self.maxTxsNum=filters['maxTxsNum']
        self.minAvg=filters['minAvg']
        self.maxAvg=filters['maxAvg']
        self.save()

    def getFilters(self):
        return FiltersModel(self).filters

    def addNode(self, name, addr, filters):
        if self.session.uuid != Coin.objects.filter(name__iexact=self.session.coin.name).first().sessions.first().uuid:
            try:
                self.session.isUniqNode(name, addr)
                node = self.nodes.create(name=name, addr=addr, group=self)
                node.setFilters(filters)
                return "Success"
            except ValidationError as e:
                print(e)

        return "ERROR"

    def getAsDict(self):
        addrs = []

        for node in self.nodes.all():
            addrs.append(node.getAsDict())

        return {
            "name": self.name,
            "url": self.getUrl(),
            "uuid": self.uuid,
            "addrs": addrs,
            "filters": FiltersModel(self).getChangedFilters()
        }

    def __str__(self):
        return self.name

class Session(models.Model):
    name = models.CharField(max_length=16, validators=[MinLengthValidator(3), RegexValidator(nameRegex)])
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    coin = models.ForeignKey('Coin', related_name='sessions', on_delete=models.CASCADE)

    def getUrl(self):
        return self.coin.getUrl() + "/" + str(self.uuid)

    def getGroup(self, id=None):
        try:
            if is_valid_uuid(id):
                return self.groups.all().get(uuid=id)
            return self.groups.all().get(name__iexact=id)
        except Group.DoesNotExist as e:
            raise Http404("Invalid Group")

    def addGroup(self, name):
        return self.groups.create(name=name, session=self)

    def isUniqGroupName(self, name):
        for group in self.groups.all():
            if group.name == name:
                raise ValidationError('{} is not unique group name in session {}'.format(name, self.name))
    
    def getNode(self, addr):
        for group in self.groups.all():
            for node in group.nodes.all():
                if node.addr == addr:
                    return node
        
        raise Http404("Invalid Address")

    def getNodes(self):
        nodes = []

        for group in self.groups.all():
            for node in group.nodes.all():
                nodes.append(node.getAsDict())
        
        return nodes
    
    def getAddrs(self):
        addrs = []

        for group in self.groups.all():
            for node in group.nodes.all():
                addrs.append(node.addr)
        
        return addrs

    def isUniqNode(self, name, addr):
        for group in self.groups.all():
            for node in group.nodes.all():
                if node.name == name:
                    raise ValidationError('{} is not unique node name in session {}'.format(name, self.name))
                if node.addr == addr:
                    raise ValidationError('{} is not unique node addr in session {}'.format(addr, self.name))
    
    def getAsDict(self):
        return {
            'name': self.name,
            'url': self.getUrl(),
            'uuid': self.uuid,
            'addrs': self.getNodes()
        }

    def getAsList(self):        
        catList    = []

        home = {
            'name': 'Home',
            'url': "/{}/search/Home?".format(self.coin.name),
            'addrs': [],
            'filters': {}
        }

        for group in self.groups.all():
            if group.name == "Home":
                temp = group.getAsDict()
                home['url'] = temp['url'] + home['url']
                home['addrs'] += temp['addrs']
                home['uuid'] = temp['uuid']
                home['filters'] = temp['filters']
                continue

            for node in group.nodes.all():
                home['addrs'].append(node.getAsDict())
                home['url'] += "&addr[]=" + node.addr

            if len(group.nodes.all()) < 1:
                continue

            catList.append(group.getAsDict())

        catList.insert(0, home)

        return catList       

    def __str__(self):
        return self.name

@receiver(post_save, sender=Session)
def created(sender, instance, created, **kwargs):
    if created:
        instance.addGroup("Home")

class Coin(models.Model):
    name = models.CharField(max_length=5, validators=[MinLengthValidator(3), RegexValidator(nameRegex)], default="USDT")

    user = models.ForeignKey(User, related_name='coins', on_delete=models.CASCADE)

    def isUniqSession(self, name):
        return not self.sessions.all().filter(name__iexact=name).exists()

    def getImg(self):
        if self.name == "USDT":
            return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMgAAADICAMAAACahl6sAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAMAUExURUxpcaXWyEiwfXG/o3XLuilqViWger3/7iahe///+CGfeCaheyCedyOgeSOfeSihfP///xucdIDMtB+edv///////yOlffj6+f///x+heSCfdx2ddabZyc3p4FK0llC0lYvOuj2wjUq6l/38/aray2O8oNru6VO7m5jRvy6rhOr49Vy5nP///2/Ap4PKtWzBpl25nR2fdoHIs1e2mE+ylM3s5ILNtvD49UixkLzk2Fm+n33HsL/m3NHr43LEq57VxmS8oV6+obTb0GTBpKTYx4fLt021laDWxU+ylG7CpxucdJXUwCahe1i4mr3i2GXCpXDEqrTe0afgzHLEq5LTv+D47+r28lq9nkCsikKzkU+4l33HsDOviHHBqfr6+nHJrUGyj33BrGfBpTSqhmq+pZTRvY7IvKPbyaDXxZfUwVO4mD2qiVK8m5zUwUKti5fTwJjSwC+kgFq2mmHCo2LCpZTRv2u/paPYx2rEqKndzUu3lnfOtK3j03fDrFu6nD2xjUO1knPIrWLAo2fBpU2xkUCrihSYbnfDrUivjkm3lhqcczaohCukf0Csi5LTvz2qiXLDqS6kgCqifV25nSahe////yiifCmifRyddRqcdB6edvz+/v7///3//kWujv7//iSgeiehe4XKtJvUwiehfCeifGW9oiqjfR+edyCfePv9/Rmbcy2vhySmfhSacILJsyqshPr9/Bebclq3myKjex2heCWogDOng/z+/WO8oSKfeXnFrk6zlBWacTCyij6sijm0jj62kS6lgDayjPj8+0OujTSxiojNtyeqgRqddev38x2ddvX7+TGviGC6nz25kyiifWq/pXPCquPz7oDIsq7czm7Apub18CWherPe0aLXx/P6+MHk2imjfd/x7Ge+o1C/nTi3kNzw6kewj8/r4lS1lzephkS4lD+8lsvp4Lfg05TRvtLs5KjZysbn3Z7WxEqxkhCYbn7HsZjTwe/49YzOuS6ogpHQvXfErF3Gpr3j11TEoovTvdXt5mPIqSeogH/uUfQAAACUdFJOUwADBAUCAfwB/gL7/fv7/f4G/MP8CQz+ER38+/ydSfHOTe/9KnDROv5N/RujI2/YpP79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'
        return ""

    def getUrl(self):
        return "/" + self.name.lower()

    def addSession(self, name, copySession=None):
        try:
            if self.isUniqSession(name):
                session = self.sessions.create(name=name, coin=self)
                print(copySession)
                if copySession:
                    for group in self.getSession(copySession).groups.all():
                        newGroup = session.groups.create(name=group.name, session=session)
                        newGroup.setFilters(group.getFilters())
                        for node in group.nodes.all():
                            newNode = newGroup.nodes.create(name=node.name, addr=node.addr, group=newGroup)
                            newNode.setFilters(node.getFilters())
                return session
        except ValidationError as e:
            pass
        
        return None

    def editSession(self, id=None, newName=""):
        session = self.getSession(id)

        try:
            if session.uuid != Coin.objects.filter(name__iexact=self.name).first().sessions.first().uuid and self.isUniqSession(newName):
                session.name = newName
                session.save()
                return "Success"
        except ValidationError as e:
            pass

        return "ERROR"

    def delSession(self, id=None):
        if id != Coin.objects.filter(name__iexact=self.name).first().sessions.first().uuid:
            try:
                session = self.sessions.all().get(uuid=id)
                session.delete()
                return "Success"
            except Exception as e:
                pass
        return "ERROR"

    def getSession(self, id=None):
        try:
            return self.sessions.all().get(uuid=id)
        except Session.DoesNotExist as e:
            return Coin.objects.filter(name__iexact=self.name).first().sessions.first()

    def getSessions(self):
        sessions = []

        for session in self.sessions.all():
            sessions.append(session.getAsDict())

        return sessions

    def __str__(self):
        return self.name