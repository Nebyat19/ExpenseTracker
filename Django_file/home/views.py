from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.shortcuts import redirect

# def index(response):
#     return render(response, "home/base.html", {})
def home(response):
    return render(response, "home/index.html", {})
    
def sign_up(request):
    return render(request, "authentication/register.html")
def login(request):
    return render(request, "authentication/login.html")