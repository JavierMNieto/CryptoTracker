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
from django.db import IntegrityError
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
		isValidName(username)
		isValidEmail(email)
		isValidPassword(password)
		if password != confirmPass:
			raise ValidationError("Password and confirmation password are not equal!", code="invalid")

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

		return HttpResponse("Success. Please confirm your email address to complete the registration.")
	except IntegrityError as e:
		if "username" in str(e):
			return HttpResponse("ERROR! Username is not unique!")
		elif "email" in str(e):
			return HttpResponse("ERROR! Email is not unique!")
	except ValidationError as e:
		return HttpResponse("ERROR! " + e.message)

	return HttpResponse("ERROR")

def forgotPass(request):
	email = request.POST.get("email", "")

	try:
		validate_email(email)
		
		if not isUsedEmail(email):
			raise ValidationError("No account uses " + email + "!", code="invalid")

		user = User.objects.get(email=email)

		message = render_to_string("tracker/resetpass_email.html", {
			'user': user,
			'domain': get_current_site(request).domain,
			'uid': urlsafe_base64_encode(force_bytes(user.pk)),
			'token': acct_activation_token.make_token(user),
		})

		email = EmailMessage("Password Change for Cryptotracker Account.", body=message, to=[email])

		email.send()

		return HttpResponse("Success. Please check your email address for a link to change your password.")
	except ValidationError as e:
		return HttpResponse("ERROR! " + e.message)

	return HttpResponse("ERROR")

def passChange(request, uidb64, token):
	signout(request)

	try:
		uid  = urlsafe_base64_decode(uidb64).decode()
		user = User.objects.get(pk=uid)
	except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
		return home(request, rejection="Invalid user id!")

	if request.method == "GET":		
		if acct_activation_token.check_token(user, token):
			return home(request)

		return home(request, rejection="Password change link is invalid!")

	elif request.method == "POST":
		if acct_activation_token.check_token(user, token):
			password 	= request.POST.get("pass", "")
			confirmPass = request.POST.get("confirmPass", "")

			try:
				isValidPassword(password)
				if password != confirmPass:
					raise ValidationError("Password and confirmation password are not equal!", code="invalid")
				user.set_password(password)
				
				return redirect("/")
			except ValidationError as e:
				return home(request, rejection="Error! " + e.message)
		
		return home(request, rejection="Error! Invalid token!")

def activate(request, uidb64, token):
	try:
		uid  = urlsafe_base64_decode(uidb64).decode()
		user = User.objects.get(pk=uid)
	except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
		return home(request, rejection="Invalid user id!")
	
	if acct_activation_token.check_token(user, token):
		user.is_active = True
		user.save()

		login(request, user)

		return home(request, confirmation="Thank you for your email confirmation.")	
	
	return home(request, rejection="Activation link is invalid!")	 

def login(request, user):
	if user is not None and user.is_active:
		auth.login(request, user)
		return HttpResponse("Success")
	elif not user.is_active:
		return HttpResponse("ERROR! Please activate your account!")

	return HttpResponse("ERROR! Incorrect credentials!")

def signin(request):
	username = request.POST.get('name', '')
	password = request.POST.get('pass', '')
	user = auth.authenticate(username=username, password=password)

	return login(request, user)

def signout(request):
	auth.logout(request)
	return JsonResponse("Success", safe=False)

def acctSettings(request):
	if request.user.is_authenticated:
		return home(request)
	
	return redirect("/")

def isValidPassword(password):
	if len(password) < 32 and len(password) > 5:
		return True
	raise ValidationError("Invalid password!", code="invalid")

def isValidEmail(email):
	validate_email(email)

	if isUsedEmail(email):
		raise ValidationError(email + " is already being used!", code="invalid")

def isValidName(name):
	if len(name) < 16 and len(name) > 2 and re.match(r'^[A-Za-z0-9_ -]*$', name) != None:
		return True
	raise ValidationError(name + " is not a valid username!", code="invalid")

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