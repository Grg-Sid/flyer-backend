from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, UserSmtpCredsView

urlpatterns = [
    path("api/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/login/refresh", TokenRefreshView.as_view(), name="token_refresh_pair"),
    path("api/register/", RegisterView.as_view(), name="sign_up"),
    path("api/smtp-creds/", UserSmtpCredsView.as_view(), name="smtp-creds"),
]
