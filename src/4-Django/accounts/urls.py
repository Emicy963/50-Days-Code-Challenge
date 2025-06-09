from django.urls import path
from . import views

urlpatterns = [
    # URLs existentes (se houver)
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # API URLs
    path(
        "api/auth/login/", views.CustomTokenObtainPairView.as_view(), name="api_login"
    ),
    path(
        "api/auth/refresh/", views.CustomTokenRefreshView.as_view(), name="api_refresh"
    ),
    path("api/auth/logout/", views.LogoutView.as_view(), name="api_logout"),
    path("api/auth/register/", views.RegisterView.as_view(), name="api_register"),
    path(
        "api/auth/verify-token/",
        views.TokenVerifyView.as_view(),
        name="api_verify_token",
    ),
    # Profile URLs
    path("api/profile/", views.UserCompleteProfileView.as_view(), name="api_profile"),
    path(
        "api/profile/details/",
        views.UserProfileDetailView.as_view(),
        name="api_profile_details",
    ),
    path(
        "api/profile/image/",
        views.ProfileImageUploadView.as_view(),
        name="api_profile_image",
    ),
    # Password URLs
    path(
        "api/password/change/",
        views.ChangePasswordView.as_view(),
        name="api_change_password",
    ),
    path(
        "api/password/reset/",
        views.PasswordResetView.as_view(),
        name="api_password_reset",
    ),
    # User info
    path("api/user-info/", views.user_info, name="api_user_info"),
]
