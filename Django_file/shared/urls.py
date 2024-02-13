from django.contrib import admin
from django.urls import path
from django.urls import re_path
from shared import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  
]
