from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.auth_combined_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
]
