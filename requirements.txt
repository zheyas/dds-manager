import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from dds_app.models import Category, SubCategory

@pytest.mark.django_db
def test_home_view(client):
    url = reverse("home")
    resp = client.get(url)
    assert resp.status_code == 200

@pytest.mark.django_db
def test_auth_combined_view_get(client):
    url = reverse("auth")
    resp = client.get(url)
    assert resp.status_code == 200

@pytest.mark.django_db
def test_registration_success(client):
    url = reverse("auth")
    data = {
        "form_type": "register",
        "username": "pytestuser",
        "password1": "pytestP@ss1234",
        "password2": "pytestP@ss1234",
    }
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200
    assert User.objects.filter(username="pytestuser").exists()

@pytest.mark.django_db
def test_login_success(client, django_user_model):
    user = django_user_model.objects.create_user(username="pytestlogin", password="pytestpass")
    url = reverse("auth")
    data = {
        "form_type": "login",
        "username": "pytestlogin",
        "password": "pytestpass",
    }
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200

@pytest.mark.django_db
def test_login_fail(client):
    url = reverse("auth")
    data = {
        "form_type": "login",
        "username": "noexist",
        "password": "noexist",
    }
    resp = client.post(url, data)
    assert resp.status_code == 200
    assert "Неверные данные" in resp.content.decode() or resp.context['login_form'].errors


@pytest.mark.django_db
def test_logout_view(client, django_user_model):
    user = django_user_model.objects.create_user(username="logout1", password="logout1")
    client.login(username="logout1", password="logout1")
    url = reverse("logout")
    resp = client.post(url, follow=True)
    assert resp.redirect_chain
    assert resp.status_code == 200

@pytest.mark.django_db
def test_get_quotes(client, monkeypatch):
    class MockResp:
        status_code = 200
        def json(self):
            return {
                "Valute": {
                    "USD": {"Value": 77.23},
                    "EUR": {"Value": 88.19},
                }
            }
    monkeypatch.setattr("requests.get", lambda *_a, **_k: MockResp())
    url = reverse("get_quotes")
    resp = client.get(url)
    assert resp.status_code == 200
    js = resp.json()
    assert "usd_rub" in js and "eur_rub" in js

@pytest.mark.django_db
def test_profile_view(client, django_user_model):
    user = django_user_model.objects.create_user(username="prof", password="profpass")
    client.login(username="prof", password="profpass")
    url = reverse("profile")
    resp = client.get(url)
    assert resp.status_code == 200

@pytest.mark.django_db
def test_get_subcategories(client, django_user_model):
    user = django_user_model.objects.create_user(username="abc", password="def")
    cat = Category.objects.create(name="На еду", type="expense")
    SubCategory.objects.create(name="KFC", category=cat)
    client.login(username="abc", password="def")
    url = reverse("get_subcategories")
    resp = client.get(url, {"category_id": cat.id})
    assert resp.status_code == 200
    assert resp.json()[0]["name"] == "KFC"

@pytest.mark.django_db
def test_get_categories_by_type(client, django_user_model):
    user = django_user_model.objects.create_user(username="d1", password="d2")
    cat = Category.objects.create(name="Дивиденды", type="income")
    client.login(username="d1", password="d2")
    url = reverse("get_categories_by_type")
    resp = client.get(url, {"type": "income"})
    assert resp.status_code == 200
    assert resp.json()[0]["name"] =="Дивиденды"

# Проверка split_rub_kop
def test_split_rub_kop():
    from dds_app.views import split_rub_kop
    assert split_rub_kop(1234.56) == ("1 234", "56")
    assert split_rub_kop(7.01) == ("7", "01")
    assert split_rub_kop(-0.009) == ("0", "01")
