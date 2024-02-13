from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Category, Budget, Duration
from expenses.models import Notification
# Create your views here.
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
import json
from django.http import JsonResponse
from userpreferences.models import UserPreference
import datetime
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist

# Create your views here.
@login_required(login_url='/authentication/login')
def index(request):
    categories = Category.objects.all()
    durations = Duration.objects.all()
    budget = Budget.objects.filter(owner=request.user)
    paginator = Paginator(budget, 5)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    try:
        user_preference = UserPreference.objects.get(user=request.user)
        currency = user_preference.currency
    except ObjectDoesNotExist:
        # Handle the case when UserPreference does not exist for the user
        currency = 'ETB'
    my_number = Notification.objects.filter(owner=request.user).count()
    user = request.user  # Assuming the user is authenticated
    notifications = Notification.objects.filter(owner=user)
    

    user = request.user  # Assuming you have a user object available in the request

    # Calculate the start and end dates for the desired time intervals
    today = timezone.now().date()
    one_week_ago = today - timedelta(days=7)
    one_month_ago = today - timedelta(days=30)

    # Get all categories for the user
    # categories = Category.objects.filter(owner=user).values_list('name', flat=True)

    category = Category.objects.values_list('name', flat=True)
    # Query the Budget table to sum amounts per category for each time interval, filtered by user
    daily_amounts = Budget.objects.filter(owner=user, date=today).values('category').annotate(total_amount=Sum('amount'))
    weekly_amounts = Budget.objects.filter(owner=user, date__gte=one_week_ago, date__lte=today).values('category').annotate(total_amount=Sum('amount'))
    monthly_amounts = Budget.objects.filter(owner=user, date__gte=one_month_ago, date__lte=today).values('category').annotate(total_amount=Sum('amount'))

    # Create dictionaries to store the amounts
    daily_data = {category: 0 for category in category}
    weekly_data = {category: 0 for category in category}
    monthly_data = {category: 0 for category in category}

    # Update the amounts for the available categories
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
    
    
    
    # Get all durations for the user
    durations = Duration.objects.values_list('names', flat=True)

    # Query the Budget table to sum amounts per duration for each time interval, filtered by user
    daily_amounts = Budget.objects.filter(owner=user, date=today).values('duration').annotate(total_amount=Sum('amount'))
    weekly_amounts = Budget.objects.filter(owner=user, date__gte=one_week_ago, date__lte=today).values('duration').annotate(total_amount=Sum('amount'))
    monthly_amounts = Budget.objects.filter(owner=user, date__gte=one_month_ago, date__lte=today).values('duration').annotate(total_amount=Sum('amount'))

    # Create dictionaries to store the amounts
    daily_data = {duration: 0 for duration in durations}
    weekly_data = {duration: 0 for duration in durations}
    monthly_data = {duration: 0 for duration in durations}

    # Update the amounts for the available durations
    for amount in daily_amounts:
        daily_data[amount['duration']] = amount['total_amount']

    for amount in weekly_amounts:
        weekly_data[amount['duration']] = amount['total_amount']

    for amount in monthly_amounts:
        monthly_data[amount['duration']] = amount['total_amount']

    # Convert the dictionaries to lists
    daily_data_list = [daily_data[duration] for duration in durations]
    weekly_data_list = [weekly_data[duration] for duration in durations]
    monthly_data_list = [monthly_data[duration] for duration in durations]

    chart_data_duration = {
    "categories": list(durations),
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
        "categories": list(durations),
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
        'budget': budget,
        'page_obj': page_obj,
        'currency': currency,
        'my_number': my_number,
        'notifications': notifications,
        'chart_data': chart_data,
        'chart_data_duration': chart_data_duration,
        'chart_data_average': chart_data_average,
    }
    return render(request, 'budget/index.html', context)


def search_budget(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        budget = Budget.objects.filter(
            amount__istartswith=search_str, owner=request.user) | Budget.objects.filter(
            date__istartswith=search_str, owner=request.user) | Budget.objects.filter(
            description__icontains=search_str, owner=request.user) | Budget.objects.filter(
            category__icontains=search_str, owner=request.user)

        data = budget.values()
        return JsonResponse(list(data), safe=False)

@login_required(login_url='/authentication/login')
def add_budget(request):
    categories = Category.objects.all()
    durations = Duration.objects.all()
    my_number = Notification.objects.filter(owner=request.user).count()
    user = request.user  # Assuming the user is authenticated
    notifications = Notification.objects.filter(owner=user)
    context = {
        'categories': categories,
        'durations':durations,
        'values': request.POST,
        'my_number': my_number,
        'notifications': notifications
    }
    if request.method == 'GET':
        return render(request, 'budget/add_budget.html', context)

    if request.method == 'POST':
        amount = request.POST['amount']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'budget/add_budget.html', context)
        duration = request.POST['duration']
        description = request.POST['description']
        date = request.POST['budget_date']
        category = request.POST['category']

        if not description:
            messages.error(request, 'description is required')
            return render(request, 'budget/add_budget.html', context)

        Budget.objects.create(owner=request.user, amount=amount, date=date,
                               duration=duration, category=category, description=description)
        messages.success(request, 'budget saved successfully')

        return redirect('budget')
    



@login_required(login_url='/authentication/login')
def budget_edit(request, id):
    budget = Budget.objects.get(pk=id)
    categories = Category.objects.all()
    durations = Duration.objects.all()
    my_number = Notification.objects.filter(owner=request.user).count()
    user = request.user  # Assuming the user is authenticated
    notifications = Notification.objects.filter(owner=user)  
    context = {
        'budget': budget,
        'values': budget,
        'categories': categories,
        'durations': durations,
        'my_number': my_number,
        'notifications': notifications
    }
    if request.method == 'GET':
        return render(request, 'budget/edit-budget.html', context)
    if request.method == 'POST':
        amount = request.POST['amount']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'budget/edit-budget.html', context)
        description = request.POST['description']
        date = request.POST['budget_date']
        category = request.POST['category']
        duration = request.POST['duration']


        if not description:
            messages.error(request, 'description is required')
            return render(request, 'budget/edit-budget.html', context)

        budget.owner = request.user
        budget.amount = amount
        budget. date = date
        budget.category = category
        budget.description = description
        budget.duration = duration

        budget.save()
        messages.success(request, 'Budget updated  successfully')

        return redirect('budget')

def delete_budget(request, id):
    budget = Budget.objects.get(pk=id)
    budget.delete()
    messages.success(request, 'Budget removed')
    return redirect('budget')

def notification_delete(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    
    if request.method == 'POST':
        notification.delete()
        # Optionally, you can add a success message or perform other actions
        
    return redirect('budget')