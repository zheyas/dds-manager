from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm


def handle_user_login(request):
    """
    Возвращает (user, login_form, error):
    либо залогиненного пользователя, либо None.
    """
    login_form = AuthenticationForm(request, data=request.POST)
    if login_form.is_valid():
        user = login_form.get_user()
        auth_login(request, user)
        return user, login_form, None
    else:
        return None, login_form, "Ошибка логина: проверьте введённые данные"


def handle_user_registration(request):
    """
    Возвращает (user, register_form, error):
    либо зарегистрированного пользователя, либо None.
    """
    register_form = UserCreationForm(request.POST)
    if register_form.is_valid():
        user = register_form.save()
        auth_login(request, user)
        return user, register_form, None
    else:
        return (None, register_form, "Ошибка регистрации: проверьте введённые данные")
