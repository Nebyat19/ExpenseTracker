from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Budget, Duration, Category
# Register your models here.


class BudgetAdmin(admin.ModelAdmin):
    list_display = ('amount', 'description', 'owner','duration', 'category', 'date',)
    search_fields = ('description', 'category', 'date',)

    list_per_page = 5


admin.site.register(Budget, BudgetAdmin)
admin.site.register(Duration)
admin.site.register(Category)
