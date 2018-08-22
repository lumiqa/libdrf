from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    url(r'^user', views.UserView.as_view(), name='current-user'),

    # JWT auth
    url(r'^login$', views.LoginView.as_view(), name='login'),
    url(r'^logout$', views.LogoutView.as_view(), name='logout'),
    url(r'^register$', views.RegistrationView.as_view(), name='register'),
    url(r'^unregister$', views.UnregistrationView.as_view(), name='unregister'),
    url(r'^register/resend$', views.ResendActivationView.as_view(), name='resend-activation'),
    url(r'^activate$', views.ActivationView.as_view(), name='activate'),
    url(r'^password/reset$', views.ResetPasswordView.as_view(), name='reset-password'),
    url(r'^password$', views.ChangePasswordView.as_view(), name='change-password'),

    # Social token exchange
    url(r'^validate/google$', views.GoogleTokenExhangeView.as_view(), name='validate_google_token'),
    url(r'^validate/facebook$', views.FacebookTokenExhangeView.as_view(), name='validate_facebook_token'),

    # Rendered email templates
    url(r'^email/activation$', TemplateView.as_view(template_name='cred/email-activation-inline.html')),
]
