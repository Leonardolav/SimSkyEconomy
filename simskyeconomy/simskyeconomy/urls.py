from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from sistema.views.login.login import LoginView, PasswordResetView, ResetPasswordView, ResendVerificationEmailView
from sistema.views.login.signup import SignupView, VerifyEmailView
from sistema.views.user.homeuser import Homeuser
from sistema.views.user.bank import BankView
from sistema.views.user.settingsprofile import ProfileView, SettingsView
from sistema.views.user.reputation import ReputationView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', LoginView.as_view(), name='login'),
    path('userhome/<int:user_id>/', Homeuser.as_view(), name='userhome'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('passwordreset/<str:token>/', ResetPasswordView.as_view(), name='reset_password'),
    path('verify-email/<uuid:token>/', VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification-email/<int:user_id>/', ResendVerificationEmailView.as_view(), name='resend_verification_email'),
    path('bank/<int:user_id>/', BankView.as_view(), name='bank'),
    path('profile/<int:user_id>/', ProfileView.as_view(), name='profile'),
    path('settings/<int:user_id>/', SettingsView.as_view(), name='settings'),
    path('reputation/<int:user_id>/', ReputationView.as_view(), name='reputation'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
