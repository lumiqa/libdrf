from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path(r'user', views.UserView.as_view(), name='current-user'),

    # JWT auth
    path(r'login', views.LoginView.as_view(), name='login'),
    path(r'logout', views.LogoutView.as_view(), name='logout'),
    path(r'register', views.RegistrationView.as_view(), name='register'),
    path(r'unregister', views.UnregistrationView.as_view(), name='unregister'),
    path(r'register/resend', views.ResendActivationView.as_view(), name='resend-activation'),
    path(r'activate', views.ActivationView.as_view(), name='activate'),
    path(r'password/reset', views.ResetPasswordView.as_view(), name='reset-password'),
    path(r'password', views.ChangePasswordView.as_view(), name='change-password'),

    # Social token exchange
    path(r'validate/google', views.GoogleTokenExhangeView.as_view(), name='validate_google_token'),
    path(r'validate/facebook', views.FacebookTokenExhangeView.as_view(), name='validate_facebook_token'),

    # Rendered email templates
    path(r'email/activation', TemplateView.as_view(template_name='login/email-activation-inline.html')),
]
