import pytest
from django.urls import reverse

from dds_app.models import Category, SubCategory


@pytest.mark.django_db
def test_home_view(client):
    url = reverse("home")
    resp = client.get(url)
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
def test_get_subcategories(client, django_user_model):
    django_user_model.objects.create_user(username="abc", password="def")
    cat = Category.objects.create(name="На еду", type="expense")
    SubCategory.objects.create(name="KFC", category=cat)
    client.login(username="abc", password="def")
    url = reverse("get_subcategories")
    resp = client.get(url, {"category_id": cat.id})
    assert resp.status_code == 200
    assert resp.json()[0]["name"] == "KFC"


@pytest.mark.django_db
def test_get_categories_by_type(client, django_user_model):
    django_user_model.objects.create_user(username="d1", password="d2")
    Category.objects.create(name="Дивиденды", type="income")
    client.login(username="d1", password="d2")
    url = reverse("get_categories_by_type")
    resp = client.get(url, {"type": "income"})
    assert resp.status_code == 200
    assert resp.json()[0]["name"] == "Дивиденды"


def test_split_rub_kop():
    from .services import split_rub_kop

    assert split_rub_kop(1234.56) == (1234, 56)
    assert split_rub_kop(7.01) == (7, 1)
    assert split_rub_kop(-0.009) == (0, -1)
