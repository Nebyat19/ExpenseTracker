from django.urls import path
from . import views

from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('', views.index, name="budget"),
    path('add-budget', views.add_budget, name="add-budget"),
    path('edit-budget/<int:id>', views.budget_edit, name="budget-edit"),
    path('budget-delete/<int:id>', views.delete_budget, name="budget-delete"),
    path('search-budget', csrf_exempt(views.search_budget), name="search_budget"),
    path('notifications/delete/<int:pk>/', views.notification_delete, name='notification_delete'),
]