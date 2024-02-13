from . import views
from django.urls import path
from django.contrib import admin
# from wallet.views import notifications_view

urlpatterns = [
    path('', views.index, name="wallet"),
    path('notifications/delete/<int:pk>/', views.notification_delete, name='notification_delete'),
    #  path('', views.notifications_view, name='notifications'),


]
