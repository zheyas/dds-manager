import pytest
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.mark.django_db
def test_auth_combined_view_get(client):
    url = reverse("login")
    resp = client.get(url)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_registration_success(client):
    url = reverse("login")
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
    django_user_model.objects.create_user(username="pytestlogin", password="pytestpass")
    url = reverse("login")
    data = {
        "form_type": "login",
        "username": "pytestlogin",
        "password": "pytestpass",
    }
    resp = client.post(url, data, follow=True)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_login_fail(client):
    url = reverse("login")
    data = {
        "form_type": "login",
        "username": "noexist",
        "password": "noexist",
    }
    resp = client.post(url, data)
    assert resp.status_code == 200
    assert (
        "Неверные данные" in resp.content.decode() or resp.context["login_form"].errors
    )


@pytest.mark.django_db
def test_logout_view(client, django_user_model):
    django_user_model.objects.create_user(username="logout1", password="logout1")
    client.login(username="logout1", password="logout1")
    url = reverse("logout")
    resp = client.post(url, follow=True)
    assert resp.redirect_chain
    assert resp.status_code == 200


@pytest.mark.django_db
def test_profile_view(client, django_user_model):
    django_user_model.objects.create_user(username="prof", password="profpass")
    client.login(username="prof", password="profpass")
    url = reverse("profile")
    resp = client.get(url)
    assert resp.status_code == 200
