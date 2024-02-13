from django.shortcuts import render, redirect
from userincome.models import Source, UserIncome
from wallet.models import Wallet
from django.db.models.functions import ExtractMonth


from expenses.models import Category, Expense, Notification
from budget.models import Budget
from django.db.models import Sum


from django.core.paginator import Paginator
from userpreferences.models import UserPreference
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import json
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist

# Create your views here.

@login_required(login_url='/authentication/login')
def index(request):
    categories = Source.objects.all()
    income = UserIncome.objects.filter(owner=request.user)
    budget = Budget.objects.filter(owner=request.user)
    expenses = Expense.objects.filter(owner=request.user)
    
    # Combine incomes and expenses
    combined_data = list(income) + list(expenses)

    # Sort the combined data by date
    combined_data.sort(key=lambda x: x.date)

    # Paginate the combined data
    paginator = Paginator(combined_data, 5)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    
    
    # paginator = Paginator(income, 5)
    # page_number = request.GET.get('page')
    # page_obj = Paginator.get_page(paginator, page_number)
    try:
        user_preference = UserPreference.objects.get(user=request.user)
        currency = user_preference.currency
    except ObjectDoesNotExist:
        # Handle the case when UserPreference does not exist for the user
        currency = 'ETB'
    
    totalIncome = income.aggregate(total_amount=Sum('amount'))['total_amount']
    totalExpense = expenses.aggregate(total_amount=Sum('amount'))['total_amount']
    totalBudget = budget.aggregate(total_amount=Sum('amount'))['total_amount']
    
    totalIncome = totalIncome or 0
    totalExpense = totalExpense or 0
    
    
    my_number = Notification.objects.filter(owner=request.user).count()
    totalBalance = totalBalances(request)
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
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # Get all sources
    category = Category.objects.values_list('name', flat=True)

    #Query the UserIncome table to sum the amounts per source for each time interval
    daily_amounts = Expense.objects.filter(owner=request.user, date=today).values('category').annotate(total_amount=Sum('amount'))
    weekly_amounts = Expense.objects.filter(owner=request.user, date__gte=one_week_ago, date__lte=today).values('category').annotate(total_amount=Sum('amount'))
    monthly_amounts = Expense.objects.filter(owner=request.user, date__gte=one_month_ago, date__lte=today).values('category').annotate(total_amount=Sum('amount'))

    # Create dictionaries to store the amounts
    daily_data = {category: 0 for category in category}
    weekly_data = {category: 0 for category in category}
    monthly_data = {category: 0 for category in category}

    # Update the amounts for the available sources
    for amount in daily_amounts:
        daily_data[amount['category']] = amount['total_amount']

    for amount in weekly_amounts:
        weekly_data[amount['category']] = amount['total_amount']

    for amount in monthly_amounts:
        monthly_data[amount['category']] = amount['total_amount']

    # Convert the dictionaries to lists
    daily_data_list = [daily_data[category] for category in category]
    weekly_data_list = [weekly_data[category] for category in category]
    monthly_data_list = [monthly_data[category] for category in category]

    chart_data_expense = {
        "categories": list(category),
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
    
    chart_data_average_expense = {
        "categories": list(category),
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
        'wallet_1': income,
        'wallet_2': expenses,
        'page_obj': page_obj,
        'totalIncome': totalIncome,
        'totalExpense': totalExpense,
        'totalBudget': totalBudget,
        'totalBalance': totalBalance,
        'currency': currency,
        'my_number': my_number,
        'notifications': notifications,
        'chart_data': chart_data,
        'chart_data_average': chart_data_average,
        'chart_data_expense': chart_data_expense,
        'chart_data_average_expense': chart_data_average_expense,
        
    }
    return render(request, 'wallet/index.html', context)



def totalBalances(request):
    income = UserIncome.objects.filter(owner=request.user)
    totalIncome = income.aggregate(total_amount=Sum('amount'))['total_amount'] or 0
    expenses = Expense.objects.filter(owner=request.user)
    totalExpense = expenses.aggregate(total_amount=Sum('amount'))['total_amount'] or 0
    balance = totalIncome - totalExpense
    
    try:
        wallet = Wallet.objects.get(owner=request.user)
        wallet.balance = balance
        wallet.save()
    except Wallet.DoesNotExist:
        Wallet.objects.create(owner=request.user, balance=balance)
    
    return balance


# def notifications_view(request):
#     user = request.user  # Assuming the user is authenticated
#     notifications = Notification.objects.filter(owner=user)
#     context = {
#         'notifications': notifications
#     }
#     return render(request, 'wallet/index.html', context)



from django.shortcuts import redirect, get_object_or_404

def notification_delete(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    
    if request.method == 'POST':
        notification.delete()
        # Optionally, you can add a success message or perform other actions
        
    return redirect('wallet')