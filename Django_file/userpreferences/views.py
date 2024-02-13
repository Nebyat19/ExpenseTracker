from django.shortcuts import render
import os
import json
from django.conf import settings
from .models import UserPreference
from expenses.models import Notification
from django.contrib import messages
from django.contrib.auth.decorators import login_required
# Create your views here.

@login_required(login_url='/authentication/login')
def index(request):
    currency_data = []
    file_path = os.path.join(settings.BASE_DIR, 'currencies.json')

    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
        for k, v in data.items():
            currency_data.append({'name': k, 'value': v})

    exists = UserPreference.objects.filter(user=request.user).exists()
    user_preferences = None
    my_number= Notification.objects.filter(owner=request.user).count()
        
    user = request.user  # Assuming the user is authenticated
    notifications = Notification.objects.filter(owner=user)

    if exists:
        user_preferences = UserPreference.objects.get(user=request.user)
    if request.method == 'GET':

        return render(request, 'preferences/index.html', {'currencies': currency_data,
                                                          'user_preferences': user_preferences, 
                                                          'my_number': my_number,
                                                            'notifications': notifications})
    else:

        currency = request.POST['currency']
        if exists:
            user_preferences.currency = currency
            user_preferences.save()
        else:
            UserPreference.objects.create(user=request.user, currency=currency)
        messages.success(request, 'Changes saved')
        return render(request, 'preferences/index.html', {'currencies': currency_data, 'user_preferences': user_preferences, 'my_number': my_number})
    
    
from django.shortcuts import redirect, get_object_or_404
def notification_delete(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    
    if request.method == 'POST':
        notification.delete()
        # Optionally, you can add a success message or perform other actions
        
    return redirect('preferences/index.html')