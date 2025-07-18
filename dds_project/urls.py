from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dds_app.urls")),
    path("accounts/", include("users.urls")),  # кастомные логин/логаут/профиль
    # path('accounts/', include('django.contrib.auth.urls')),  # если нужны стандартные auth-urls, оставь, но могут быть конфликты с users.urls
]
