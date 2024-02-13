from . import views
from django.urls import path

urlpatterns = [
    path('', views.index, name="preferences"),
    path('notifications/delete/<int:pk>/', views.notification_delete, name='notification_delete'),

]
