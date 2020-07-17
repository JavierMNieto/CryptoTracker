"""
	Probably worth checking out new angular https://angular.io/ for easy backend and frontend compatibility
"""
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

def num_with_commas(num):
	return ("{:,}".format(float(num)))

def signup(request):
	if request.method != "POST":
		raise Http404("Only POSTs are allowed!")
	
	username 	= request.POST.get("user", "")
	password 	= request.POST.get("pass", "")
	confirmPass = request.POST.get("confirmPass", "")
	email	 	= request.POST.get("email", "")

	try:
		is_valid_name(username)
		is_valid_email(email)
		is_valid_password(password)
		if password != confirmPass:
			raise ValidationError("Password and confirmation password are not equal!", code="invalid")

		user 		  = User.objects.create_user(username=username, email=email, password=password)
		user.is_active = False
		user.save()

		return verify_email(request, force_text(urlsafe_base64_encode(force_bytes(user.pk))))
	except IntegrityError as e:
		if "username" in str(e):
			return HttpResponse("ERROR! Username is not unique!")
		elif "email" in str(e):
			return HttpResponse("ERROR! Email is not unique!")
	except ValidationError as e:
		return HttpResponse("ERROR! " + e.message)

	return HttpResponse("ERROR")

def forgot_pass(request):
	email = request.POST.get("email", "")

	try:
		validate_email(email)
		
		if not is_used_email(email):
			raise ValidationError("No account uses " + email + "!", code="invalid")

		user = User.objects.get(email=email)

		message = render_to_string("tracker/resetpass_email.html", {
			'user': user,
			'domain': get_current_site(request).domain,
			'uid': force_text(urlsafe_base64_encode(force_bytes(user.pk))),
			'token': acct_activation_token.make_token(user),
		})

		email = EmailMessage("Password Change for Cryptotracker Account.", body=message, to=[email])

		email.send()

		return HttpResponse("Success. Please check your email address for a link to change your password.")
	except ValidationError as e:
		return HttpResponse("ERROR! " + e.message)

	return HttpResponse("ERROR")

def pass_change(request, uidb64, token):
	signout(request)

	try:
		uid  = urlsafe_base64_decode(uidb64)
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
				is_valid_password(password)
				if password != confirmPass:
					raise ValidationError("Password and confirmation password are not equal!", code="invalid")
				user.set_password(password)
				
				return redirect("/")
			except ValidationError as e:
				return home(request, rejection="Error! " + e.message)
		
		return home(request, rejection="Error! Invalid token!")

def activate(request, uidb64, token):
	try:
		uid  = urlsafe_base64_decode(uidb64)
		user = User.objects.get(pk=uid)
	except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
		return home(request, rejection="Invalid user id!")
	
	if acct_activation_token.check_token(user, token):
		user.is_active = True
		user.save()

		login(request, user)

		return home(request, confirmation="Thank you for your email confirmation.")	
	
	return home(request, rejection="Activation link is invalid!")	 

def verify_email(request, uidb64):
	try:
		uid  = urlsafe_base64_decode(uidb64)
		user = User.objects.get(pk=uid)
	except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
		print(e)
		return HttpResponse("ERROR! Invalid User!")

	message = render_to_string("tracker/activate_email.html", {
		'user': user,
		'domain': get_current_site(request).domain,
		'uid': uidb64,
		'token': acct_activation_token.make_token(user),
	})

	email = EmailMessage("Activate Cryptotracker Account.", body=message, to=[user.email])
	email.send()

	return HttpResponse("Success. Please check your email address for a link to change your password.")

def login(request, user):
	if user is not None and user.is_active:
		auth.login(request, user)
		return HttpResponse("Success")
	elif user is not None and not user.is_active:
		response = """ERROR! Please activate your account! <button class="btn btn-primary" onclick="main.submit('verify_email', `{}`)">Click to Resend Email</button>""".format(force_text(urlsafe_base64_encode(force_bytes(user.pk))))
		return HttpResponse(response)

	return HttpResponse("ERROR! Incorrect credentials!")

def signin(request):
	username = request.POST.get('name', '')
	password = request.POST.get('pass', '')

	user = None

	try:
		is_valid_email(username)
	except ValidationError as e:
		if e.code == "used":
			user = auth.authenticate(username=User.objects.filter(email=username).first().username, password=password)
		else:
			user = auth.authenticate(username=username, password=password)

	return login(request, user)

def signout(request):
	auth.logout(request)
	return JsonResponse("Success", safe=False)

def acct_settings(request):
	if request.user.is_authenticated:
		return home(request)
	
	return redirect("/")

def is_valid_password(password):
	if len(password) < 32 and len(password) > 5:
		return True
	raise ValidationError("Invalid password!", code="invalid")

def is_valid_email(email):
	validate_email(email)

	if is_used_email(email):
		raise ValidationError(email + " is already being used!", code="used")

def is_valid_name(name):
	if len(name) < 16 and len(name) > 2 and re.match(r'^[A-Za-z0-9_ -]*$', name) != None:
		return True
	raise ValidationError(name + " is not a valid username!", code="invalid")

def is_uniq_email(request):
	return JsonResponse(not is_used_email(request.GET.get("email", "")), safe=False)

def is_used_email(email):
	return User.objects.filter(email=email).exists()

def is_uniq_user_name(request):
	return JsonResponse(not User.objects.filter(username__iexact=request.GET.get("username")).exists(), safe=False)

def home(request, confirmation=None, rejection=None):
	cmc = ccxt.coinbase()
	btc = cmc.fetch_ticker('BTC/USD')
	return render(request, 'tracker/index.html', {
		'search': [], 
		'coin': None, 
		'homeUrl': '#', 
		'btc': btc,
		'confirmation': confirmation, 
		'rejection': rejection
	})