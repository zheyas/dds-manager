import math
import requests
from django.db.models import Sum, F, ExpressionWrapper, FloatField
from .models import CashFlow

def split_rub_kop(amount):
    """
    Делит сумму на рубли и копейки (23.99 → 23, 99).
    """
    rub = int(amount)
    kop = int(round((amount - rub) * 100))
    return rub, kop

def fetch_cbr_quotes(timeout=5):
    """
    Получает курсы валют USD и EUR (рубли) с сайта ЦБРФ.
    Возвращает кортеж (usd_rub, eur_rub). В случае ошибки возвращает (None, None).
    """
    try:
        resp = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            usd_rub = round(data["Valute"]["USD"]["Value"], 2)
            eur_rub = round(data["Valute"]["EUR"]["Value"], 2)
            return usd_rub, eur_rub
    except Exception:
        pass
    return None, None

def get_floor_cashback(amount, cashback_percent):
    """
    Округление кэшбэка вниз (floor).
    """
    return math.floor(amount * cashback_percent / 100)

def annotate_cashflow_with_cashback(cashflows):
    """
    Добавляет каждому объекту CashFlow поле cashback_floor (только для расходов).
    """
    for op in cashflows:
        if op.type == "expense" and op.cashback_percent:
            op.cashback_floor = get_floor_cashback(op.amount, op.cashback_percent)
        else:
            op.cashback_floor = 0
    return cashflows

def get_cashflow_stat(user, type_, date_from, date_to):
    """
    Возвращает сумму и сумму кэшбэка за период по типу операции.
    """
    qs = CashFlow.objects.filter(
        user=user, type=type_,
        created_at__gte=date_from,
        created_at__lt=date_to
    )
    total = qs.aggregate(amount=Sum("amount"))["amount"] or 0
    cashback = qs.aggregate(
        cashback=Sum(
            ExpressionWrapper(
                F("amount") * F("cashback_percent") / 100,
                output_field=FloatField()
            )
        )
    )["cashback"] or 0
    return total, cashback
