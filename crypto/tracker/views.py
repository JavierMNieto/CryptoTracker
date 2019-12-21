from django.http import HttpResponse, Http404, HttpResponseForbidden, JsonResponse
from django.template import loader
from neo4j.v1 import GraphDatabase
from django.contrib.auth.models import User
from django.core.validators import validate_email, ValidationError
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import auth
from django.core.mail import EmailMessage
from .tokens import acct_activation_token
from coin.models import Coin
import ccxt
import json
import time
import math
import requests
import sys
import re
import traceback

sys.path.append("../")
from static.py.clean import *

def numWithCommas(num):
	return ("{:,}".format(float(num)))

def signup(request):
	if request.method != "POST":
		raise Http404("Only POSTs are allowed!")
	
	username 	= request.POST.get("user", "")
	password 	= request.POST.get("pass", "")
	confirmPass = request.POST.get("confirmPass", "")
	email	 	= request.POST.get("email", "")

	try:
		if isValidName(username) and isValidEmail(email) and isValidPassword(password) and password == confirmPass:
			user 		  = User.objects.create_user(username=username, email=email, password=password)
			user.is_active = False
			user.save()

			message = render_to_string("tracker/activate_email.html", {
				'user': user,
                'domain': get_current_site(request).domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': acct_activation_token.make_token(user),
			})

			email = EmailMessage("Activate Cryptotracker Account.", body=message, to=[email])
			email.send()

			return HttpResponse("Success")
	except Exception as e:
		traceback.print_exc(e)

	return HttpResponse("ERROR")

def forgotPass(request):
	email = request.POST.get("email", "")

	if isValidEmail(email) and isUsedEmail(email):
		user = User.objects.get(email=email)

		message = render_to_string("tracker/resetpass_email.html", {
			'user': user,
			'domain': get_current_site(request).domain,
			'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
			'token': acct_activation_token.make_token(user),
		})

		email = EmailMessage("Password Change for Cryptotracker Account.", body=message, to=[email])

		email.send()

		return HttpResponse("Success")

	return HttpResponse("ERROR")

def passChange(request, uidb64, token):
	try:
		uid  = urlsafe_base64_decode(uidb64).decode()
		user = User.objects.get(pk=uid)
	except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
		print(e)
		user = None

	if request.method == "GET":		
		if user is not None and acct_activation_token.check_token(user, token):
			return home(request)

		return home(request, rejection="Password change link is invalid!")
	elif request.method == "POST":
		if user is not None and acct_activation_token.check_token(user, token):
			password 	= request.POST.get("pass", "")
			confirmPass = request.POST.get("confirmPass", "")

			if isValidPassword(password) and password == confirmPass:
				user.set_password(password)
				
				return redirect("/")
		
		return home(request, rejection="Error!")

def activate(request, uidb64, token):
	try:
		uid  = urlsafe_base64_decode(uidb64).decode()
		user = User.objects.get(pk=uid)
	except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
		print(e)
		user = None
	
	if user is not None and acct_activation_token.check_token(user, token):
		user.is_active = True
		user.save()

		login(request, user)

		return home(request, confirmation="Thank you for your email confirmation.")	
	
	return home(request, rejection="Activation link is invalid!")	 

def login(request, user):
	if user is not None and user.is_active:
		auth.login(request, user)
		return HttpResponse("Success")

	return HttpResponse("ERROR")

def signin(request):
	username = request.POST.get('name', '')
	password = request.POST.get('pass', '')
	user = auth.authenticate(username=username, password=password)

	return login(request, user)

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
	return JsonResponse(not isUsedEmail(request.GET.get("email", "")), safe=False)

def isUsedEmail(email):
	return User.objects.filter(email=email).exists()

def isUniqUserName(request):
	return JsonResponse(not User.objects.filter(username__iexact=request.GET.get("username")).exists(), safe=False)

def home(request, confirmation=None, rejection=None):
	cmc = ccxt.coinmarketcap()
	btc = cmc.fetch_ticker('BTC/USD')
	return render(request, 'tracker/index.html', {
		'search': [], 
		'coin': None, 
		'homeUrl': '#', 
		'btc': btc,
		'confirmation': confirmation, 
		'rejection': rejection
	})