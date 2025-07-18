import datetime

from django import forms
from django.utils import timezone

from .models import CashFlow, Category, Status, SubCategory


class StatusForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": "form-control"})}


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "type"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "type": forms.Select(attrs={"class": "form-select"}),
        }


class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ["name", "category"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
        }


class CashFlowForm(forms.ModelForm):
    # Скрытое поле для типа операции
    type = forms.CharField(widget=forms.HiddenInput(), required=True)

    def __init__(self, *args, **kwargs):
        type_ = kwargs.pop("type", None)
        if "initial" not in kwargs:
            kwargs["initial"] = {}
        if type_ is not None:
            kwargs["initial"]["type"] = type_
        super().__init__(*args, **kwargs)

        # Форматируем дату/время для виджета datetime-local
        self.fields["created_at"].widget = forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format="%Y-%m-%dT%H:%M",
        )
        self.fields["created_at"].input_formats = ["%Y-%m-%dT%H:%M"]

        if self.instance and getattr(self.instance, "created_at", None):
            self.initial["created_at"] = self.instance.created_at.strftime(
                "%Y-%m-%dT%H:%M"
            )
        elif self.initial.get("created_at") and isinstance(
            self.initial["created_at"], datetime.datetime
        ):
            self.initial["created_at"] = self.initial["created_at"].strftime(
                "%Y-%m-%dT%H:%M"
            )
        elif not self.initial.get("created_at"):
            now = timezone.localtime(timezone.now())
            self.initial["created_at"] = now.strftime("%Y-%m-%dT%H:%M")

        # Если тип "расход", включаем cashback_percent, иначе скрываем
        if self.initial.get("type") == "expense":
            self.fields["cashback_percent"].required = True
            self.fields["cashback_percent"].widget.attrs.update(
                {"placeholder": "0-100", "min": 0, "max": 100, "class": "form-control"}
            )
        else:
            self.fields["cashback_percent"].required = False
            self.fields["cashback_percent"].widget = forms.HiddenInput()

    class Meta:
        model = CashFlow
        fields = [
            "title",
            "created_at",
            "status",
            "category",
            "subcategory",
            "amount",
            "type",
            "cashback_percent",
            "comment",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "subcategory": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "type": forms.HiddenInput(),
            "cashback_percent": forms.NumberInput(attrs={"class": "form-control"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        exclude = ["user"]

    def clean_cashback_percent(self):
        type_ = self.cleaned_data.get("type")
        cashback = self.cleaned_data.get("cashback_percent")
        if type_ == "expense":
            if cashback is None:
                raise forms.ValidationError(
                    "Для трат обязательно" " укажите кешбэк (если его нет — укажите 0)."
                )
            if cashback < 0 or cashback > 100:
                raise forms.ValidationError("Кешбэк должен быть от 0 до 100.")
        else:
            if cashback not in (None, 0):
                raise forms.ValidationError("Кешбэк можно указывать только для трат.")
            return None
        return cashback

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")
        type_ = cleaned_data.get("type")
        subcategory = cleaned_data.get("subcategory")

        if category is None:
            self.add_error("category", "Обязательное поле: категория.")
        else:
            if type_ and category.type != type_:
                self.add_error(
                    "category", "Тип категории и " "тип операции должны совпадать."
                )
            if subcategory and subcategory.category_id != category.id:
                self.add_error(
                    "subcategory", "Подкатегория не " "принадлежит выбранной категории."
                )
        return cleaned_data
