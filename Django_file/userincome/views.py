from django.shortcuts import render, redirect
from .models import Source, UserIncome
from expenses.models import Notification
from django.core.paginator import Paginator
from userpreferences.models import UserPreference
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import json
from django.http import JsonResponse

from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist

# Create your views here.


def search_income(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        income = UserIncome.objects.filter(
            amount__istartswith=search_str, owner=request.user) | UserIncome.objects.filter(
            date__istartswith=search_str, owner=request.user) | UserIncome.objects.filter(
            description__icontains=search_str, owner=request.user) | UserIncome.objects.filter(
            source__icontains=search_str, owner=request.user)
        data = income.values()
        return JsonResponse(list(data), safe=False)


@login_required(login_url='/authentication/login')
def index(request):
    categories = Source.objects.all()
    income = UserIncome.objects.filter(owner=request.user)
    paginator = Paginator(income, 5)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    try:
        user_preference = UserPreference.objects.get(user=request.user)
        currency = user_preference.currency
    except ObjectDoesNotExist:
        # Handle the case when UserPreference does not exist for the user
        currency = 'ETB'
    my_number= Notification.objects.filter(owner=request.user).count()
    user = request.user  # Assuming the user is authenticated
    notifications = Notification.objects.filter(owner=user)
    
    # category = [source.name for source in Source.objects.all()]
    # Calculate the start and end dates for the desired time intervals
    today = timezone.now().date()
    one_week_ago = today - timedelta(days=7)
    one_month_ago = today - timedelta(days=30)

    # Get all sources
    all_sources = Source.objects.values_list('name', flat=True)

    # Query the UserIncome table to sum the amounts per source for each time interval
    daily_amounts = UserIncome.objects.filter(owner=request.user, date=today).values('source').annotate(total_amount=Sum('amount'))
    weekly_amounts = UserIncome.objects.filter(owner=request.user, date__gte=one_week_ago, date__lte=today).values('source').annotate(total_amount=Sum('amount'))
    monthly_amounts = UserIncome.objects.filter(owner=request.user, date__gte=one_month_ago, date__lte=today).values('source').annotate(total_amount=Sum('amount'))

    # Create dictionaries to store the amounts
    daily_data = {source: 0 for source in all_sources}
    weekly_data = {source: 0 for source in all_sources}
    monthly_data = {source: 0 for source in all_sources}

    # Update the amounts for the available sources
    for amount in daily_amounts:
        daily_data[amount['source']] = amount['total_amount']

    for amount in weekly_amounts:
        weekly_data[amount['source']] = amount['total_amount']

    for amount in monthly_amounts:
        monthly_data[amount['source']] = amount['total_amount']

    # Convert the dictionaries to lists
    daily_data_list = [daily_data[source] for source in all_sources]
    weekly_data_list = [weekly_data[source] for source in all_sources]
    monthly_data_list = [monthly_data[source] for source in all_sources]

    chart_data = {
        "categories": list(all_sources),
        "series": [
            {
                "name": "Today",
                "data": daily_data_list
            },
            {
                "name": "This Week",
                "data": weekly_data_list
            },
            {
                "name": "This Month",
                "data": monthly_data_list
            }
        ]
    }
    
    chart_data_average = {
        "categories": list(all_sources),
        "series": [
            {
                "name": "Average",
                "data": [
                    sum(daily_data_list) / len(daily_data_list) if len(daily_data_list) > 0 else 0,
                    sum(weekly_data_list) / len(weekly_data_list) if len(weekly_data_list) > 0 else 0,
                    sum(monthly_data_list) / len(monthly_data_list) if len(monthly_data_list) > 0 else 0
                ]
            }
        ]
    }
    
    context = {
        'income': income,
        'page_obj': page_obj,
        'currency': currency,
        'my_number': my_number,
        'notifications': notifications,
        'chart_data': chart_data,
        'chart_data_average': chart_data_average,
    }
    
    return render(request, 'income/index.html', context)


@login_required(login_url='/authentication/login')
def add_income(request):
    sources = Source.objects.all()
    my_number = Notification.objects.filter(owner=request.user).count()
    user = request.user  # Assuming the user is authenticated
    notifications = Notification.objects.filter(owner=user)
    
    context = {
        'sources': sources,
        'values': request.POST,
        'my_number': my_number,
        'notifications': notifications
    }
    if request.method == 'GET':
        return render(request, 'income/add_income.html', context)

    if request.method == 'POST':
        amount = request.POST['amount']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'income/add_income.html', context)
        description = request.POST['description']
        date = request.POST['income_date']
        source = request.POST['source']

        if not description:
            messages.error(request, 'description is required')
            return render(request, 'income/add_income.html', context)

        UserIncome.objects.create(owner=request.user, amount=amount, date=date,
                                  source=source, description=description)
        messages.success(request, 'Record saved successfully')

        return redirect('income')


@login_required(login_url='/authentication/login')
def income_edit(request, id):
    income = UserIncome.objects.get(pk=id)
    sources = Source.objects.all()
    my_number = Notification.objects.filter(owner=request.user).count()
    user = request.user  # Assuming the user is authenticated
    notifications = Notification.objects.filter(owner=user)
    
    context = {
        'income': income,
        'values': income,
        'sources': sources,
        'my_number': my_number,
        'notifications': notifications
    }
    if request.method == 'GET':
        return render(request, 'income/edit_income.html', context)
    if request.method == 'POST':
        amount = request.POST['amount']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'income/edit_income.html', context)
        description = request.POST['description']
        date = request.POST['income_date']
        source = request.POST['source']

        if not description:
            messages.error(request, 'description is required')
            return render(request, 'income/edit_income.html', context)
        income.amount = amount
        income. date = date
        income.source = source
        income.description = description

        income.save()
        messages.success(request, 'Record updated  successfully')

        return redirect('income')


def delete_income(request, id):
    income = UserIncome.objects.get(pk=id)
    income.delete()
    messages.success(request, 'record removed')
    return redirect('income')

def notification_delete(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    
    if request.method == 'POST':
        notification.delete()
        # Optionally, you can add a success message or perform other actions
        
    return redirect('income')