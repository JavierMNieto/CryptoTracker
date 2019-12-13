from django.http import HttpResponse, Http404, HttpResponseForbidden, JsonResponse
from django.template import loader
from neo4j.v1 import GraphDatabase
from django.contrib.auth.models import User
from django.core.validators import validate_email, ValidationError
from django.shortcuts import render
from django.contrib import auth
from coin.models import Coin
import ccxt
import json
import time
import math
import requests
import sys
import re

sys.path.append("../")
from static.py.clean import *

def numWithCommas(num):
	return ("{:,}".format(float(num)))

def signup(request):
	if request.method != "POST":
		raise Http404("Only POSTs are allowed!")
	
	username = request.POST.get("user")
	password = request.POST.get("pass")
	email	 = request.POST.get("email")

	try:
		if isValidName(username) and isValidPassword(password) and isValidEmail(email):
			user 		  = User.objects.create_user(username=username, email=email, password=password)
			user.is_valid = False
			user.save()

			user = auth.authenticate(username=username, password=password)
			if user is not None and user.is_active:
				auth.login(request, user)
				return HttpResponse("Success")
	except Exception as e:
		pass

	return HttpResponse("ERROR")

def signin(request):
	username = request.POST.get('name', '')
	password = request.POST.get('pass', '')
	user = auth.authenticate(username=username, password=password)
	if user is not None and user.is_active:
		auth.login(request, user)
		return HttpResponse("Success")
	
	return HttpResponse("ERROR")

def signout(request):
	auth.logout(request)
	return HttpResponse("Success")

def isValidPassword(password):
	return len(password) < 32 and len(password) > 5

def isValidName(name):
	return len(name) < 16 and len(name) > 2 and re.match(r'^[A-Za-z0-9_ -]*$', name) != None

def isValidEmail(email):
	try:
		validate_email(email)
		return True
	except ValidationError:
		return False

def isUniqEmail(request):
	return JsonResponse(not User.objects.filter(email__iexact=request.GET.get("email")).exists(), safe=False)

def isUniqUserName(request):
	return JsonResponse(not User.objects.filter(username__iexact=request.GET.get("username")).exists(), safe=False)

def home(request):
	cmc = ccxt.coinmarketcap()
	btc = cmc.fetch_ticker('BTC/USD')
	return render(request, 'tracker/index.html', {'search': [], 'coin': None, 'homeUrl': '#', 'btc': btc})