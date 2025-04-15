import re
from django.views import View
from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import JsonResponse
from sistema.models import UserProfile, ReputationLevel, Currency, EmailVerificationToken
from django.utils import timezone
import requests
from django.urls import reverse

class SignupView(View):
    def get(self, request):
        return render(request, 'signup.html')

    def post(self, request):
        if request.htmx:  
            username = request.POST.get('username')
            email = request.POST.get('email')
            response_data = {'username_error': '', 'email_error': ''}

            if username and User.objects.filter(username=username).exists():
                response_data['username_error'] = 'Username already in use'
            if email and User.objects.filter(email=email).exists():
                response_data['email_error'] = 'Email already in use'

            return JsonResponse(response_data)

        try:
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')

            if not username or not password or not first_name or not last_name or not email:
                return JsonResponse({'success': False, 'error': 'All fields are required'})

            if not (3 <= len(username) <= 30):
                return JsonResponse({'success': False, 'error': 'Username must be between 3 and 30 characters'})

            if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
                return JsonResponse({'success': False, 'error': 'Invalid email format'})

            if not (3 <= len(first_name) <= 30):
                return JsonResponse({'success': False, 'error': 'First name must be between 3 and 30 characters'})
            
            if not (3 <= len(last_name) <= 30):
                return JsonResponse({'success': False, 'error': 'Last name must be between 3 and 30 characters'})

                # Check if username or email is already in use
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': 'Username already in use'})
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'error': 'Email already in use'})

            reputation_level, currency = None, None
            try:
                reputation_level = ReputationLevel.objects.get(reputation_grade='F-')
            except ReputationLevel.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Initial reputation level not found.'})
            try:
                currency = Currency.objects.get(code='USD')
            except Currency.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Default currency not found.'})

            with transaction.atomic():


                user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
                
                reputation_level = ReputationLevel.objects.get(reputation_grade='F-')
                currency = Currency.objects.get(code='USD')
                
                user_profile = UserProfile.objects.create(
                    user=user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    registration_date=timezone.now(),
                    reputation_level=reputation_level,
                    score=0,
                    first_access=True,
                    email_verified=False,  # Email not verified initially
                    preferred_currency=currency,
                    cash_balance = 5000.00,
                )
            
                
                # Welcome email
                welcome_html = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                        <h2>Welcome to SimSky Economy, {first_name}!</h2>
                        <p>Hello {username},</p>
                        <p>We are thrilled to welcome you to SimSky Economy! Your account has been successfully created, and you're now part of our growing community.</p>
                        <p>Here's what you can look forward to:</p>
                        <ul>
                            <li>Explore exciting economic simulations</li>
                            <li>Build your reputation starting from level F-</li>
                            <li>Interact with a vibrant community</li>
                        </ul>
                        <p>Get started by logging in with your username: <strong>{username}</strong> or your email: <strong>{email}</strong>.</p>
                        <p>Please verify your email address to fully activate your account (see the verification email we just sent).</p>
                        <p>If you have any questions, feel free to reach out to our support team.</p>
                        <p>Best regards,<br>The SimSky Economy Team</p>
                    </body>
                </html>
                """
                welcome_data = {
                    'email': email,
                    'assunto': 'Your Journey Begins: Welcome to SimSky Economy!',
                    'texto': welcome_html
                }
                requests.post('https://n8n.leonardolavourinha.com/webhook/1cd32f77-6428-491e-86ad-818f63524319', json=welcome_data)

                # Verification email
                verification_token = EmailVerificationToken.objects.create(user=user)
                verification_link = request.build_absolute_uri(reverse('verify_email', args=[str(verification_token.token)]))
                verification_html = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                        <h2>Verify Your Email Address</h2>
                        <p>Hello {username},</p>
                        <p>Thank you for signing up with SimSky Economy!</p>
                        <p>To complete your registration, please verify your email address by clicking the link below:</p>
                        <p><a href="{verification_link}">{verification_link}</a></p>
                        <p>This link will expire in 30 minutes.</p>
                        <p>If you did not create an account, please ignore this email.</p>
                        <p>Best regards,<br>The SimSky Economy Team</p>
                    </body>
                </html>
                """
                verification_data = {
                    'email': email,
                    'assunto': 'Please Verify Your SimSky Economy Email',
                    'texto': verification_html
                }
                response = requests.post(
                    'https://n8n.leonardolavourinha.com/webhook/1cd32f77-6428-491e-86ad-818f63524319',
                    json=verification_data
                )
                
                if response.status_code != 200:
                    print(f"Verification email webhook failed with status {response.status_code}: {response.text}")
                
                return JsonResponse({'success': True})
        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'An error occurred during user creation.'})
        except Exception:
            return JsonResponse({'success': False, 'error': 'An unexpected error occurred.'})

from django.db import IntegrityError, transaction
class VerifyEmailView(View):
    def get(self, request, token):
        try:
            verification_token = EmailVerificationToken.objects.get(token=token)
            if verification_token.is_expired():
                verification_token.delete()
                return render(request, 'verify_email.html', {'error': 'This verification link has expired.'})
            return render(request, 'verify_email.html', {'token': token})
        except EmailVerificationToken.DoesNotExist:
            return render(request, 'verify_email.html', {'error': 'Invalid verification link.'})

    def post(self, request, token):
        try:
            verification_token = EmailVerificationToken.objects.get(token=token)
            if verification_token.is_expired():
                verification_token.delete()
                return JsonResponse({'success': False, 'error': 'This verification link has expired.'})
            
            user = verification_token.user
            user_profile = UserProfile.objects.get(user=user)
            user_profile.email_verified = True
            user_profile.save()

            # Confirmation email
            confirmation_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <h2>Email Verified Successfully, {user.first_name}!</h2>
                    <p>Hello {user.username},</p>
                    <p>Your email address has been successfully verified for SimSky Economy.</p>
                    <p>You can now log in with your username: <strong>{user.username}</strong> or your email: <strong>{user_profile.email}</strong>.</p>
                    <p>Welcome aboard! Enjoy all the features of SimSky Economy.</p>
                    <p>Best regards,<br>The SimSky Economy Team</p>
                </body>
            </html>
            """
            confirmation_data = {
                'email': user_profile.email,
                'assunto': 'Your SimSky Economy Email is Now Verified!',
                'texto': confirmation_html
            }
            response = requests.post(
                'https://n8n.leonardolavourinha.com/webhook/1cd32f77-6428-491e-86ad-818f63524319',
                json=confirmation_data
            )
            
            if response.status_code != 200:
                print(f"Confirmation email webhook failed with status {response.status_code}: {response.text}")
            
            verification_token.delete()
            return JsonResponse({'success': True})
        except EmailVerificationToken.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid verification link.'})
        except UserProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User profile not found.'})