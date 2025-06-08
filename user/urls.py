from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenObtainPairView, MeView, RegisterView, api_root

urlpatterns = [
    path("", api_root, name="api-root"),
    path("users/", RegisterView.as_view(), name="register"),
    path("users/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("users/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("users/me/", MeView.as_view(), name="user_me"),
]

app_name = "users"