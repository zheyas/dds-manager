#dds_app/views.py
import math
import logging
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import CashFlow, Status, Category, SubCategory
from .forms import CashFlowForm, StatusForm, CategoryForm, SubCategoryForm
from django.http import JsonResponse
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login as auth_login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum, F, ExpressionWrapper, FloatField
from django.utils import timezone
import requests
from django.contrib.auth import logout

logger = logging.getLogger("dds_app")

def logout_view(request):
    logout(request)
    return redirect('home')

def split_rub_kop(amount):
    rub = int(amount)
    kop = int(round((abs(amount) - abs(rub)) * 100))
    # Если округление до 100 копеек, повышаем рубль!
    if kop == 100:
        rub = rub + 1 if amount >= 0 else rub - 1
        kop = 0
    # Тыс разделитель
    return f"{rub:,}".replace(",", " "), f"{kop:02d}"

def auth_combined_view(request):
    login_form = AuthenticationForm()
    register_form = UserCreationForm()
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'login':
            login_form = AuthenticationForm(request, data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                auth_login(request, user)
                return redirect('profile')
        elif form_type == 'register':
            register_form = UserCreationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                auth_login(request, user)
                return redirect('profile')
    return render(request, 'registration/login.html', {
        'login_form': login_form,
        'register_form': register_form,
    })

def get_quotes(request):
    usd_rub, eur_rub = "—", "—"
    try:
        resp = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            usd_rub = round(data["Valute"]["USD"]["Value"], 2)
            eur_rub = round(data["Valute"]["EUR"]["Value"], 2)
    except Exception as e:
        logger.infologger.info("CBR exception:", e)
    return JsonResponse({
        "usd_rub": f"₽ {usd_rub}",
        "eur_rub": f"₽ {eur_rub}",
    })

class CashFlowListView(LoginRequiredMixin, ListView):
    model = CashFlow
    template_name = 'dds_app/cashflow_list.html'
    context_object_name = 'cashflows'
    paginate_by = 30

    def get_queryset(self):
        qs = CashFlow.objects.filter(user=self.request.user) \
            .select_related('user', 'status', 'category', 'subcategory')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        status = self.request.GET.get('status')
        self.type_ = self.request.GET.get('type')
        category = self.request.GET.get('category')
        subcategory = self.request.GET.get('subcategory')
        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)
        if status:
            qs = qs.filter(status_id=status)
        if self.type_:
            qs = qs.filter(type=self.type_)
        if category:
            qs = qs.filter(category_id=category)
        if subcategory:
            qs = qs.filter(subcategory_id=subcategory)
        return qs.order_by('-created_at', '-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = Status.objects.all()
        if self.type_:
            context['categories'] = Category.objects.filter(type=self.type_)
        else:
            context['categories'] = Category.objects.all()
        context['subcategories'] = SubCategory.objects.all()
        context['type_choices'] = Category.TYPE_CHOICES
        context['filter'] = {
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
'status': self.request.GET.get('status', ''),
            'type': self.type_ or '',
            'category': self.request.GET.get('category', ''),
            'subcategory': self.request.GET.get('subcategory', ''),
        }
        return context

class CashFlowCreateIncomeView(LoginRequiredMixin, CreateView):
    model = CashFlow
    template_name = 'dds_app/cashflow_form.html'
    form_class = CashFlowForm
    success_url = reverse_lazy('cashflow_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['type'] = 'income'
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = 'income'
        context['categories'] = Category.objects.filter(type='income')
        category_id = self.request.POST.get('category') or self.request.GET.get('category')
        if category_id:
            try:
                context['subcategories'] = SubCategory.objects.filter(category_id=category_id)
            except Category.DoesNotExist:
                context['subcategories'] = SubCategory.objects.none()
        else:
            context['subcategories'] = SubCategory.objects.none()
        return context

    def form_valid(self, form):
        logger.info("[CREATE INCOME] cleaned_data:", form.cleaned_data)
        logger.info("[CREATE INCOME] POST data:", dict(self.request.POST))
        form.instance.user = self.request.user
        form.instance.type = 'income'
        messages.success(self.request, "Операция успешно сохранена.")
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.info("[CREATE INCOME] POST data:", dict(self.request.POST))
        logger.info("[CREATE INCOME] form.errors:", form.errors)
        messages.error(self.request, "Ошибка сохранения операции. Проверьте правильность заполнения формы.")
        return self.render_to_response(self.get_context_data(form=form))

class CashFlowCreateExpenseView(LoginRequiredMixin, CreateView):
    model = CashFlow
    template_name = 'dds_app/cashflow_form.html'
    form_class = CashFlowForm
    success_url = reverse_lazy('cashflow_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['type'] = 'expense'
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = 'expense'
        context['categories'] = Category.objects.filter(type='expense')
        category_id = self.request.POST.get('category') or self.request.GET.get('category')
        if category_id:
            try:
                context['subcategories'] = SubCategory.objects.filter(category_id=category_id)
            except Category.DoesNotExist:
                context['subcategories'] = SubCategory.objects.none()
        else:
            context['subcategories'] = SubCategory.objects.none()
        return context

    def form_valid(self, form):
        logger.info("[CREATE EXPENSE] cleaned_data:", form.cleaned_data)
        logger.info("[CREATE EXPENSE] POST data:", dict(self.request.POST))
        form.instance.user = self.request.user
        form.instance.type = 'expense'
        messages.success(self.request, "Операция успешно сохранена.")
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.info("[CREATE EXPENSE] POST data:", dict(self.request.POST))
        logger.info("[CREATE EXPENSE] form.errors:", form.errors)
        messages.error(self.request, "Ошибка сохранения операции. Проверьте правильность заполнения формы.")
        return self.render_to_response(self.get_context_data(form=form))

class CashFlowUpdateView(LoginRequiredMixin, UpdateView):
    model = CashFlow
    form_class = CashFlowForm
    template_name = 'dds_app/cashflow_form.html'
    success_url = reverse_lazy('cashflow_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['type'] = self.get_object().type
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cashflow = self.get_object()
        context['type'] = cashflow.type
        context['categories'] = Category.objects.filter(type=cashflow.type)
        category_id = self.request.POST.get('category') or (cashflow.category_id if cashflow.category else None)
        if category_id:
            try:
                context['subcategories'] = SubCategory.objects.filter(category_id=category_id)
            except Category.DoesNotExist:
                context['subcategories'] = SubCategory.objects.none()
        else:
            context['subcategories'] = SubCategory.objects.none()
        return context

    def form_valid(self, form):
        logger.info("[UPDATE CASHFLOW] cleaned_data:", form.cleaned_data)
        logger.info("[UPDATE CASHFLOW] POST data:", dict(self.request.POST))
        messages.success(self.request, "Операция успешно обновлена.")
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.info("[UPDATE CASHFLOW] POST data:", dict(self.request.POST))
        logger.info("[UPDATE CASHFLOW] form.errors:", form.errors)
        messages.error(self.request, "Ошибка обновления операции. Проверьте правильность заполнения формы.")
        return self.render_to_response(self.get_context_data(form=form))

class CashFlowDeleteView(LoginRequiredMixin, DeleteView):
    model = CashFlow
    template_name = 'dds_app/cashflow_confirm_delete.html'
    success_url = reverse_lazy('cashflow_list')

# --- CRUD для справочников ---

class StatusListView(LoginRequiredMixin, ListView):
    model = Status
    template_name = 'dds_app/status_list.html'
    context_object_name = 'statuses'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.prefetch_related('subcategories').all()
        return context
class StatusCreateView(LoginRequiredMixin, CreateView):
    model = Status
    form_class = StatusForm
    template_name = 'dds_app/status_form.html'
    success_url = reverse_lazy('status_list')
class StatusUpdateView(LoginRequiredMixin, UpdateView):
    model = Status
    form_class = StatusForm
    template_name = 'dds_app/status_form.html'
    success_url = reverse_lazy('status_list')
class StatusDeleteView(LoginRequiredMixin, DeleteView):
    model = Status
    template_name = 'dds_app/status_confirm_delete.html'
    success_url = reverse_lazy('status_list')
class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'dds_app/category_list.html'
    context_object_name = 'categories'
class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'dds_app/category_form.html'
    success_url = reverse_lazy('category_list')
class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'dds_app/category_form.html'
    success_url = reverse_lazy('category_list')
class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'dds_app/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')
class SubCategoryListView(LoginRequiredMixin, ListView):
    model = SubCategory
    template_name = 'dds_app/subcategory_list.html'
    context_object_name = 'subcategories'
class SubCategoryCreateView(LoginRequiredMixin, CreateView):
    model = SubCategory
    form_class = SubCategoryForm
    template_name = 'dds_app/subcategory_form.html'
    success_url = reverse_lazy('subcategory_list')
class SubCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = SubCategory
    form_class = SubCategoryForm
    template_name = 'dds_app/subcategory_form.html'
    success_url = reverse_lazy('subcategory_list')
class SubCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = SubCategory
    template_name = 'dds_app/subcategory_confirm_delete.html'
    success_url = reverse_lazy('subcategory_list')

@login_required
def profile_view(request):
    user = request.user
    today = timezone.localdate()
    month_start = today.replace(day=1)
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)

    # Доходы
    income_qs = CashFlow.objects.filter(
        user=user, type="income",
        created_at__gte=month_start,
        created_at__lt=next_month
    )
    income_sum = income_qs.aggregate(amount=Sum("amount"))["amount"] or 0
    income_cashback = income_qs.aggregate(
        cashback=Sum(ExpressionWrapper(F("amount") * F("cashback_percent") / 100, output_field=FloatField()))
    )["cashback"] or 0

    # Расходы
    expense_qs = CashFlow.objects.filter(
        user=user, type="expense",
        created_at__gte=month_start,
        created_at__lt=next_month
    )
    expense_sum = expense_qs.aggregate(amount=Sum("amount"))["amount"] or 0
    expense_cashback = expense_qs.aggregate(
        cashback=Sum(ExpressionWrapper(F("amount") * F("cashback_percent") / 100, output_field=FloatField()))
    )["cashback"] or 0

    # Последние операции
    latest_ops = CashFlow.objects.filter(user=user).order_by('-created_at', '-id')[:5]

    # Для каждой операции считаем "floor cashback" для расходов
    for op in latest_ops:
        if op.type == "expense" and op.cashback_percent:
            cashback = math.floor(op.amount * op.cashback_percent / 100)
            # Можно сразу положить к объекту (например, op.cashback_display = ...)
            op.cashback_floor = cashback
        else:
            op.cashback_floor = 0

    # Форматируем суммы для шаблона
    def split_rub_kop(amount):
        rub = int(amount)
        kop = int(round((abs(amount) - abs(rub)) * 100))
        if kop == 100:
            rub = rub + 1 if amount >= 0 else rub - 1
            kop = 0
        return f"{rub:,}".replace(",", " "), f"{kop:02d}"

    income_rub, income_kop = split_rub_kop(income_sum)
    income_cashback_rub, income_cashback_kop = split_rub_kop(income_cashback)
    expense_rub, expense_kop = split_rub_kop(expense_sum)
    expense_cashback_rub, expense_cashback_kop = split_rub_kop(expense_cashback)

    return render(request, "dds_app/index.html", {
        "income_rub": income_rub,
        "income_kop": income_kop,
        "income_cashback_rub": income_cashback_rub,
        "income_cashback_kop": income_cashback_kop,
        "expense_rub": expense_rub,
        "expense_kop": expense_kop,
        "expense_cashback_rub": expense_cashback_rub,
        "expense_cashback_kop": expense_cashback_kop,
        "latest_ops": latest_ops,
    })

@login_required
def get_subcategories(request):
    category_id = request.GET.get('category_id')
    subcats = []
    if category_id:
        subcats = list(SubCategory.objects.filter(category_id=category_id).values('id', 'name'))
    return JsonResponse(subcats, safe=False)

def home(request):
    return render(request, 'dds_app/home.html')

@login_required
def get_categories_by_type(request):
    type_ = request.GET.get('type')
    cats = []
    if type_:
        cats = list(Category.objects.filter(type=type_).values('id', 'name'))
    return JsonResponse(cats, safe=False)