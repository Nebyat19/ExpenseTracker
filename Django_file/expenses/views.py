from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Category, Expense, Notification
from wallet.models import Wallet
from budget.models import Budget
# Create your views here.
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
import json
from django.http import JsonResponse
from userpreferences.models import UserPreference
import datetime
from django.db.models import Sum
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

def search_expenses(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        expenses = Expense.objects.filter(
            amount__istartswith=search_str, owner=request.user) | Expense.objects.filter(
            category__icontains=search_str, owner=request.user) | Expense.objects.filter(
            description__icontains=search_str, owner=request.user) | Expense.objects.filter(
            date__istartswith=search_str, owner=request.user) 
        data = expenses.values()
        return JsonResponse(list(data), safe=False)


@login_required(login_url='/authentication/login')
def index(request):
    categories = Category.objects.all()
    expenses = Expense.objects.filter(owner=request.user)
    paginator = Paginator(expenses, 5)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    try:
        user_preference = UserPreference.objects.get(user=request.user)
        currency = user_preference.currency
    except ObjectDoesNotExist:
        # Handle the case when UserPreference does not exist for the user
        currency = 'default_currency'
    
    my_number = Notification.objects.filter(owner=request.user).count()
    user=request.user
    notifications = Notification.objects.filter(owner=user)
    
    # category = [category.name for category in Category.objects.all()]
    # Calculate the start and end dates for the desired time intervals
    today = timezone.now().date()
    one_week_ago = today - timedelta(days=7)
    one_month_ago = today - timedelta(days=30)

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

    chart_data = {
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
    
    chart_data_average = {
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
        'expenses': expenses,
        'page_obj': page_obj,
        'currency': currency,
        'my_number': my_number,
        'notifications': notifications,
        'chart_data': chart_data,
        'chart_data_average': chart_data_average,
    }
    return render(request, 'expenses/index.html', context)


@login_required(login_url='/authentication/login')
def add_expense(request):
    categories = Category.objects.all()
    
    my_number = Notification.objects.filter(owner=request.user).count()
    user = request.user  # Assuming the user is authenticated
    notifications = Notification.objects.filter(owner=user)
    context = {
        'categories': categories,
        'values': request.POST,
        'my_number': my_number,
        'notifications': notifications
    }
    if request.method == 'GET':
        return render(request, 'expenses/add_expense.html', context)

    if request.method == 'POST':
        amount = request.POST['amount']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/add_expense.html', context)

        # Retrieve all Budget objects associated with the user
        budgets = Budget.objects.filter(owner=request.user)

        if budgets.exists():
            # Use the first Budget object found
            budget = budgets.first()

            if float(amount) > budget.amount:
                messages.warning(request, 'Spending Over Budget')
                message = "You Spent Over Your Budget"
                current_time = datetime.now().time()
                con= {
                    'message': message,
                    'time': current_time
                }
                notify(con, request)
        else:
            # If no Budget objects found, create a new one
            budget = Budget.objects.create(owner=request.user, amount=0)
        # Check if Wallet exists for the user, and create one if it doesn't
        try:
            wallet = Wallet.objects.get(owner=request.user)
        except Wallet.DoesNotExist:
            wallet = Wallet.objects.create(owner=request.user, balance=0)
        if float(amount) > wallet.balance:
            messages.error(request, 'Balance Insufficient')
            message = "You Tried To Overspend"
            current_time = datetime.now().time()
            con= {
                'message': message,
                'time': current_time
            }
            notify(con, request)
            return render(request, 'expenses/add_expense.html', context)

        description = request.POST['description']
        date = request.POST['expense_date']
        category = request.POST['category']

        if not description:
            messages.error(request, 'description is required')
            return render(request, 'expenses/add_expense.html', context)

        Expense.objects.create(owner=request.user, amount=amount, date=date,
                               category=category, description=description)
        messages.success(request, 'Expense saved successfully')

        return redirect('expenses')


@login_required(login_url='/authentication/login')
def expense_edit(request, id):
    expense = Expense.objects.get(pk=id)
    categories = Category.objects.all()
    my_number = Notification.objects.filter(owner=request.user).count()
    user = request.user  # Assuming the user is authenticated
    notifications = Notification.objects.filter(owner=user)
    context = {
        'expense': expense,
        'values': expense,
        'categories': categories,
        'my_number': my_number,
        'notifications': notifications
    }
    if request.method == 'GET':
        return render(request, 'expenses/edit-expense.html', context)
    if request.method == 'POST':
        amount = float(request.POST['amount'])

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/edit-expense.html', context)
        
        # Check if Wallet exists for the user, and create one if it doesn't
        try:
            budget = Budget.objects.get(owner=request.user)
        except Budget.DoesNotExist:
            budget = Budget.objects.create(owner=request.user, amount=0)
        if float(amount) > budget.amount:
            messages.warning(request, 'Spending Over Budget')
            message = "You Spent Over Your Budget"
            current_time = datetime.now().time()
            con= {
                'message': message,
                'time': current_time
            }
            notify(con, request)
        # Check if Wallet exists for the user, and create one if it doesn't
        try:
            wallet = Wallet.objects.get(owner=request.user)
        except Wallet.DoesNotExist:
            wallet = Wallet.objects.create(owner=request.user, balance=0)
        if float(amount) > wallet.balance:
            messages.error(request, 'Balance Insufficient')
            message = "You Tried To Overspend"
            current_time = datetime.now().time()
            con= {
                'message': message,
                'time': current_time
            }
            notify(con, request)
            return render(request, 'expenses/add_expense.html', context)
        description = request.POST['description']
        date = request.POST['expense_date']
        category = request.POST['category']

        if not description:
            messages.error(request, 'description is required')
            return render(request, 'expenses/edit-expense.html', context)

        expense.owner = request.user
        expense.amount = amount
        expense. date = date
        expense.category = category
        expense.description = description

        expense.save()
        messages.success(request, 'Expense updated  successfully')

        return redirect('expenses')


def delete_expense(request, id):
    expense = Expense.objects.get(pk=id)
    expense.delete()
    messages.success(request, 'Expense removed')
    return redirect('expenses')


def expense_category_summary(request):
    todays_date = datetime.date.today()
    six_months_ago = todays_date-datetime.timedelta(days=30*6)
    expenses = Expense.objects.filter(owner=request.user,
                                      date__gte=six_months_ago, date__lte=todays_date)
    finalrep = {}

    def get_category(expense):
        return expense.category
    category_list = list(set(map(get_category, expenses)))

    def get_expense_category_amount(category):
        amount = 0
        filtered_by_category = expenses.filter(category=category)

        for item in filtered_by_category:
            amount += item.amount
        return amount

    for x in expenses:
        for y in category_list:
            finalrep[y] = get_expense_category_amount(y)

    return JsonResponse({'expense_category_data': finalrep}, safe=False)


def stats_view(request):
    my_number = Notification.objects.filter(owner=request.user).count()
    user = request.user  # Assuming the user is authenticated
    notifications = Notification.objects.filter(owner=user)
    
    return render(request, 'expenses/stats.html', {'my_number': my_number, 'notifications': notifications})

def TotalBalance(request):
    # read the database for totalBalance, return balance
    # if balance < expense amount = send notification 
    wallet = Wallet.objects.get(owner=request.user)
    total_balance = wallet.aggregate(total_amount=Sum('balance'))['total_amount']    
    return total_balance or 0.0

def notify(context, request):
    message = context['message']
    time = context['time']
    Notification.objects.create(owner=request.user,message = message, time=time)    
    
    
def TotalBudget(request):
    # read the database for totalBudget, return budget
    # if budget < expense amount = send notification 
    budget = Budget.objects.filter(owner=request.user)
    total_budget = budget.aggregate(total_amount=Sum('amount'))['total_amount']    
    return float(total_budget)


def notification_delete(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    
    if request.method == 'POST':
        notification.delete()
        # Optionally, you can add a success message or perform other actions
        
    return redirect('expenses')