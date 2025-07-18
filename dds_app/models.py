#dds_app/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError

class Status(models.Model):
    name = models.CharField(max_length=64, unique=True, verbose_name="Статус")

    def __str__(self):
        return self.name


class Category(models.Model):
    TYPE_CHOICES = (
        ('income', 'Пополнение'),
        ('expense', 'Трата'),
    )
    name = models.CharField(max_length=64, verbose_name="Категория")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Тип операции")

    class Meta:
        unique_together = ('name', 'type')
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return f"{self.get_type_display()} | {self.name}"

    def clean(self):
        # При обновлении требуем минимум 3 подкатегории
        if self.pk:
            subcat_count = self.subcategories.count()
            if subcat_count < 0:
                raise ValidationError(
                    f'У категории "{self.name}" должно быть как минимум 1 подкатегории (сейчас: {subcat_count}).'
                )


class SubCategory(models.Model):
    name = models.CharField(max_length=64, verbose_name="Подкатегория")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="subcategories", verbose_name="Категория"
    )

    class Meta:
        unique_together = ('name', 'category')
        verbose_name = "Подкатегория"
        verbose_name_plural = "Подкатегории"

    def __str__(self):
        return f"{self.category} — {self.name}"


class CashFlow(models.Model):
    TYPE_CHOICES = Category.TYPE_CHOICES

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="cashflows", verbose_name="Пользователь"
    )
    title = models.CharField(max_length=128, verbose_name="Название операции")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата/Время")
    status = models.ForeignKey(
        Status, on_delete=models.CASCADE, related_name="cashflows", verbose_name="Статус"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="cashflows", verbose_name="Категория"
    )
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        related_name="cashflows",
        verbose_name="Подкатегория",
        null=True,
        blank=True,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Сумма")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Тип операции")
    cashback_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Кешбэк (%)",
        help_text="Укажите процент кешбэка, если операция — трата",
    )
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "ДДС операция"
        verbose_name_plural = "ДДС операции"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} | {self.created_at} | {self.amount} | {self.category} -> {self.subcategory}"

    def clean(self):
        errors = {}

        if not self.category_id:
            errors['category'] = 'Категория обязательно должна быть заполнена.'
        else:
            category = self.category  # безопасно, т.к. ID уже есть
            if category.type != self.type:
                errors['category'] = 'Тип категории и тип операции должны совпадать.'

        if self.subcategory and self.category_id and self.subcategory.category_id != self.category_id:
            errors['subcategory'] = 'Подкатегория не принадлежит выбранной категории.'

        if self.type == 'expense':
            if self.cashback_percent is None:
                errors['cashback_percent'] = 'Для трат кешбэк (%) обязателен.'
            elif self.cashback_percent < 0 or self.cashback_percent > 100:
                errors['cashback_percent'] = 'Кешбэк должен быть в диапазоне от 0 до 100.'
        else:
            if self.cashback_percent not in (None, 0):
                errors['cashback_percent'] = 'Кешбэк можно указывать только для трат.'
            self.cashback_percent = None  # Очистка кешбэка для доходов

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Перед сохранением вызываем clean для валидации
        self.clean()
        super().save(*args, **kwargs)

    @property
    def cashback_amount(self):
        """Вычисляемая сумма кешбэка (только для трат)."""
        if self.type != 'expense' or not self.cashback_percent:
            return Decimal('0.00')
        value = (self.amount * self.cashback_percent / 100).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        return value
