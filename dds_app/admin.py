
from django.contrib import admin
from .models import Status, Category, SubCategory, CashFlow

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type')
    list_filter = ('type',)
    search_fields = ('name',)

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(CashFlow)
class CashFlowAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'user', 'status', 'type', 'category', 'subcategory', 'amount', 'comment')
    list_filter = ('status', 'type', 'category', 'subcategory', 'user')
    search_fields = ('comment', 'amount')
    date_hierarchy = 'created_at'
