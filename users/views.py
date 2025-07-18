from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render
from django.utils import timezone

from dds_app.models import CashFlow
from dds_app.services import (
    annotate_cashflow_with_cashback,
    get_cashflow_stat,
    split_rub_kop,
)

from .services import handle_user_login, handle_user_registration


def logout_view(request):
    logout(request)
    return redirect("home")


def auth_combined_view(request):
    login_form = AuthenticationForm()
    register_form = UserCreationForm()
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "login":
            user, login_form, error = handle_user_login(request)
            if user:
                return redirect("profile")
        elif form_type == "register":
            user, register_form, error = handle_user_registration(request)
            if user:
                return redirect("profile")
    return render(
        request,
        "registration/login.html",
        {
            "login_form": login_form,
            "register_form": register_form,
        },
    )


@login_required
def profile_view(request):
    """
    View-функция профиля пользователя.

    Отображает дашборд пользователя
    с итоговой статистикой по доходам и расходам
    за текущий месяц, включая кэшбэки,
     а также последние пять операций пользователя.

    Логика работы:
        1. Получает текущего пользователя из объекта запроса.
        2. Определяет даты начала и конца текущего месяца.
        3. Считает общую сумму доходов и кэшбэков,
        и отдельно расходов и кэшбэков,
           за указанный период (текущий месяц)
           с помощью функции get_cashflow_stat.
        4. Получает 5 последних операций пользователя
         из модели CashFlow (сортировка по дате и id).
        5. Аннотирует эти операции информацией о кэшбэке.
        6. Форматирует значения сумм и кэшбэков
         для отображения (разбивая на рубли и копейки).
        7. Передает полученные данные в шаблон
        dds_app/index.html для отрисовки.

    Параметры:
        request (HttpRequest):
        HTTP-запрос пользователя.

    Возвращает:
        HttpResponse: Отрендеренный HTML
        с шаблоном dds_app/index.html и подготовленным контекстом.

    Контекст шаблона включает:
        - 'income_rub', 'income_kop': основные доходы (разбиты по частям)
        - 'income_cashback_rub', 'income_cashback_kop': кэшбэк по доходам
        - 'expense_rub', 'expense_kop': основные расходы (разбиты по частям)
        - 'expense_cashback_rub', 'expense_cashback_kop': кэшбэк по расходам
        - 'latest_ops': последние 5 операций пользователя

    Требования:
        - Пользователь должен быть аутентифицирован.
        - Должны быть доступны функции get_cashflow_stat,
        annotate_cashflow_with_cashback,
          split_rub_kop и модель CashFlow.
    """
    user = request.user
    today = timezone.localdate()
    month_start = today.replace(day=1)
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)

    income_sum, income_cashback = get_cashflow_stat(
        user, "income", month_start, next_month
    )
    expense_sum, expense_cashback = get_cashflow_stat(
        user, "expense", month_start, next_month
    )

    latest_ops = CashFlow.objects.filter(user=user).order_by("-created_at", "-id")[:5]
    annotate_cashflow_with_cashback(latest_ops)

    income_rub, income_kop = split_rub_kop(income_sum)
    income_cashback_rub, income_cashback_kop = split_rub_kop(income_cashback)
    expense_rub, expense_kop = split_rub_kop(expense_sum)
    expense_cashback_rub, expense_cashback_kop = split_rub_kop(expense_cashback)

    return render(
        request,
        "dds_app/index.html",
        {
            "income_rub": income_rub,
            "income_kop": income_kop,
            "income_cashback_rub": income_cashback_rub,
            "income_cashback_kop": income_cashback_kop,
            "expense_rub": expense_rub,
            "expense_kop": expense_kop,
            "expense_cashback_rub": expense_cashback_rub,
            "expense_cashback_kop": expense_cashback_kop,
            "latest_ops": latest_ops,
        },
    )
