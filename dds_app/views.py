import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import CashFlowForm, CategoryForm, StatusForm, SubCategoryForm
from .models import CashFlow, Category, Status, SubCategory
from .services import fetch_cbr_quotes

logger = logging.getLogger("dds_app")


def get_quotes(request):
    usd_rub, eur_rub = fetch_cbr_quotes()
    return JsonResponse(
        {
            "usd_rub": f"₽ {usd_rub if usd_rub is not None else '—'}",
            "eur_rub": f"₽ {eur_rub if eur_rub is not None else '—'}",
        }
    )


class CashFlowListView(LoginRequiredMixin, ListView):
    model = CashFlow
    template_name = "dds_app/cashflow_list.html"
    context_object_name = "cashflows"
    paginate_by = 30

    def get_queryset(self):
        qs = CashFlow.objects.filter(user=self.request.user).select_related(
            "user", "status", "category", "subcategory"
        )
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        status = self.request.GET.get("status")
        self.type_ = self.request.GET.get("type")
        category = self.request.GET.get("category")
        subcategory = self.request.GET.get("subcategory")
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
        return qs.order_by("-created_at", "-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = Status.objects.all()
        if self.type_:
            context["categories"] = Category.objects.filter(type=self.type_)
        else:
            context["categories"] = Category.objects.all()
        context["subcategories"] = SubCategory.objects.all()
        context["type_choices"] = Category.TYPE_CHOICES
        context["filter"] = {
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
            "status": self.request.GET.get("status", ""),
            "type": self.type_ or "",
            "category": self.request.GET.get("category", ""),
            "subcategory": self.request.GET.get("subcategory", ""),
        }
        return context


class CashFlowCreateIncomeView(LoginRequiredMixin, CreateView):
    model = CashFlow
    template_name = "dds_app/cashflow_form.html"
    form_class = CashFlowForm
    success_url = reverse_lazy("cashflow_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["type"] = "income"
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["type"] = "income"
        context["categories"] = Category.objects.filter(type="income")
        category_id = self.request.POST.get("category") or self.request.GET.get(
            "category"
        )
        if category_id:
            try:
                context["subcategories"] = SubCategory.objects.filter(
                    category_id=category_id
                )
            except Category.DoesNotExist:
                context["subcategories"] = SubCategory.objects.none()
        else:
            context["subcategories"] = SubCategory.objects.none()
        return context

    def form_valid(self, form):
        logger.info("[CREATE INCOME] cleaned_data: %s", form.cleaned_data)
        logger.info("[CREATE INCOME] POST data: %s", dict(self.request.POST))
        form.instance.user = self.request.user
        form.instance.type = "income"
        messages.success(self.request, "Операция успешно сохранена.")
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.info("[CREATE INCOME] POST data: %s", dict(self.request.POST))
        logger.info("[CREATE INCOME] form.errors: %s", form.errors)
        messages.error(
            self.request,
            "Ошибка сохранения операции. " "Проверьте правильность заполнения формы.",
        )
        return self.render_to_response(self.get_context_data(form=form))


class CashFlowCreateExpenseView(LoginRequiredMixin, CreateView):
    model = CashFlow
    template_name = "dds_app/cashflow_form.html"
    form_class = CashFlowForm
    success_url = reverse_lazy("cashflow_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["type"] = "expense"
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["type"] = "expense"
        context["categories"] = Category.objects.filter(type="expense")
        category_id = self.request.POST.get("category") or self.request.GET.get(
            "category"
        )
        if category_id:
            try:
                context["subcategories"] = SubCategory.objects.filter(
                    category_id=category_id
                )
            except Category.DoesNotExist:
                context["subcategories"] = SubCategory.objects.none()
        else:
            context["subcategories"] = SubCategory.objects.none()
        return context

    def form_valid(self, form):
        logger.info("[CREATE EXPENSE] cleaned_data: %s", form.cleaned_data)
        logger.info("[CREATE EXPENSE] POST data: %s", dict(self.request.POST))
        form.instance.user = self.request.user
        form.instance.type = "expense"
        messages.success(self.request, "Операция успешно сохранена.")
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.info("[CREATE EXPENSE] POST data: %s", dict(self.request.POST))
        logger.info("[CREATE EXPENSE] form.errors: %s", form.errors)
        messages.error(
            self.request,
            "Ошибка сохранения операции." "Проверьте правильность заполнения формы.",
        )
        return self.render_to_response(self.get_context_data(form=form))


class CashFlowUpdateView(LoginRequiredMixin, UpdateView):
    model = CashFlow
    form_class = CashFlowForm
    template_name = "dds_app/cashflow_form.html"
    success_url = reverse_lazy("cashflow_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["type"] = self.get_object().type
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cashflow = self.get_object()
        context["type"] = cashflow.type
        context["categories"] = Category.objects.filter(type=cashflow.type)
        category_id = self.request.POST.get("category") or (
            cashflow.category_id if cashflow.category else None
        )
        if category_id:
            try:
                context["subcategories"] = SubCategory.objects.filter(
                    category_id=category_id
                )
            except Category.DoesNotExist:
                context["subcategories"] = SubCategory.objects.none()
        else:
            context["subcategories"] = SubCategory.objects.none()
        return context

    def form_valid(self, form):
        logger.info("[UPDATE CASHFLOW] cleaned_data: %s", form.cleaned_data)
        logger.info("[UPDATE CASHFLOW] POST data: %s", dict(self.request.POST))
        messages.success(self.request, "Операция успешно обновлена.")
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.info("[UPDATE CASHFLOW] POST data: %s", dict(self.request.POST))
        logger.info("[UPDATE CASHFLOW] form.errors: %s", form.errors)
        messages.error(
            self.request,
            "Ошибка обновления операции." " Проверьте правильность заполнения формы.",
        )
        return self.render_to_response(self.get_context_data(form=form))


class CashFlowDeleteView(LoginRequiredMixin, DeleteView):
    model = CashFlow
    template_name = "dds_app/cashflow_confirm_delete.html"
    success_url = reverse_lazy("cashflow_list")


# --- CRUD для справочников ---


class StatusListView(LoginRequiredMixin, ListView):
    model = Status
    template_name = "dds_app/status_list.html"
    context_object_name = "statuses"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.prefetch_related("subcategories").all()
        return context


class StatusCreateView(LoginRequiredMixin, CreateView):
    model = Status
    form_class = StatusForm
    template_name = "dds_app/status_form.html"
    success_url = reverse_lazy("status_list")


class StatusUpdateView(LoginRequiredMixin, UpdateView):
    model = Status
    form_class = StatusForm
    template_name = "dds_app/status_form.html"
    success_url = reverse_lazy("status_list")


class StatusDeleteView(LoginRequiredMixin, DeleteView):
    model = Status
    template_name = "dds_app/status_confirm_delete.html"
    success_url = reverse_lazy("status_list")


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "dds_app/category_list.html"
    context_object_name = "categories"


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "dds_app/category_form.html"
    success_url = reverse_lazy("category_list")


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "dds_app/category_form.html"
    success_url = reverse_lazy("category_list")


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = "dds_app/category_confirm_delete.html"
    success_url = reverse_lazy("category_list")


class SubCategoryListView(LoginRequiredMixin, ListView):
    model = SubCategory
    template_name = "dds_app/subcategory_list.html"
    context_object_name = "subcategories"


class SubCategoryCreateView(LoginRequiredMixin, CreateView):
    model = SubCategory
    form_class = SubCategoryForm
    template_name = "dds_app/subcategory_form.html"
    success_url = reverse_lazy("subcategory_list")


class SubCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = SubCategory
    form_class = SubCategoryForm
    template_name = "dds_app/subcategory_form.html"
    success_url = reverse_lazy("subcategory_list")


class SubCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = SubCategory
    template_name = "dds_app/subcategory_confirm_delete.html"
    success_url = reverse_lazy("subcategory_list")


@login_required
def get_subcategories(request):
    category_id = request.GET.get("category_id")
    subcats = []
    if category_id:
        subcats = list(
            SubCategory.objects.filter(category_id=category_id).values("id", "name")
        )
    return JsonResponse(subcats, safe=False)


def home(request):
    return render(request, "dds_app/home.html")


@login_required
def get_categories_by_type(request):
    type_ = request.GET.get("type")
    cats = []
    if type_:
        cats = list(Category.objects.filter(type=type_).values("id", "name"))
    return JsonResponse(cats, safe=False)
