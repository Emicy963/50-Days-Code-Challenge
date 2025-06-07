from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    # Autenticação JWT
    path("login/", views.CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(
        "token/refresh/", views.CustomTokenRefreshView.as_view(), name="token_refresh"
    ),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("token/verify/", views.TokenVerifyView.as_view(), name="token_verify"),
    # Registro e perfil
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.UserProfileView.as_view(), name="profile"),
    path("user-info/", views.user_info, name="user_info"),
    # Mudança de senha
    path(
        "change-password/", views.ChangePasswordView.as_view(), name="change_password"
    ),
    path("password-reset/", views.PasswordResetView.as_view(), name="password_reset"),
    # URLs para frontend (opcional)
    path("me/", views.UserProfileView.as_view(), name="me"),
]
