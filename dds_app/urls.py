from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("operations/", views.CashFlowListView.as_view(), name="cashflow_list"),
    path(
        "operations/create/income/",
        views.CashFlowCreateIncomeView.as_view(),
        name="cashflow_create_income",
    ),
    path(
        "operations/create/expense/",
        views.CashFlowCreateExpenseView.as_view(),
        name="cashflow_create_expense",
    ),
    path(
        "operations/<int:pk>/edit/",
        views.CashFlowUpdateView.as_view(),
        name="cashflow_update",
    ),
    path(
        "operations/<int:pk>/delete/",
        views.CashFlowDeleteView.as_view(),
        name="cashflow_delete",
    ),
    path("statuses/", views.StatusListView.as_view(), name="status_list"),
    path("statuses/create/", views.StatusCreateView.as_view(), name="status_create"),
    path(
        "statuses/<int:pk>/edit/",
        views.StatusUpdateView.as_view(),
        name="status_update",
    ),
    path(
        "statuses/<int:pk>/delete/",
        views.StatusDeleteView.as_view(),
        name="status_delete",
    ),
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path(
        "categories/create/", views.CategoryCreateView.as_view(), name="category_create"
    ),
    path(
        "categories/<int:pk>/edit/",
        views.CategoryUpdateView.as_view(),
        name="category_update",
    ),
    path(
        "categories/<int:pk>/delete/",
        views.CategoryDeleteView.as_view(),
        name="category_delete",
    ),
    path(
        "subcategories/", views.SubCategoryListView.as_view(), name="subcategory_list"
    ),
    path(
        "subcategories/create/",
        views.SubCategoryCreateView.as_view(),
        name="subcategory_create",
    ),
    path(
        "subcategories/<int:pk>/edit/",
        views.SubCategoryUpdateView.as_view(),
        name="subcategory_update",
    ),
    path(
        "subcategories/<int:pk>/delete/",
        views.SubCategoryDeleteView.as_view(),
        name="subcategory_delete",
    ),
    path("ajax/get_subcategories/", views.get_subcategories, name="get_subcategories"),
    path("ajax/get_quotes/", views.get_quotes, name="get_quotes"),
    path(
        "ajax/get_categories_by_type/",
        views.get_categories_by_type,
        name="get_categories_by_type",
    ),
]
