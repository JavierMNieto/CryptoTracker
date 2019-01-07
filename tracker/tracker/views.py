from django.http import HttpResponse
from django.template import loader

def search(request):
	print(request)
	return HttpResponse("Hello, world. You're at the polls index.")