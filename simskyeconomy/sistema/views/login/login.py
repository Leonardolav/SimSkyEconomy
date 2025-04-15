from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from sistema.models import UserProfile, PasswordResetToken, EmailVerificationToken
from django.http import JsonResponse, HttpResponse
import requests
from django.utils import timezone
import secrets
from django.urls import reverse

class LoginView(View):
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def get_client_ip(self, request):
        # Get the client IP (supports proxies)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_geolocation(self, ip):
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}")
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    location = f"{data['city']}, {data['regionName']}, {data['country']}"
                    return location, data['lat'], data['lon']
            return "Unknown location", None, None
        except Exception as e:
            print(f"Geolocation lookup failed: {str(e)}")
            return "Unknown location", None, None

    def post(self, request, *args, **kwargs):
        identifier = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Login attempt with identifier: {identifier}")

        # Check if the identifier is an email or username
        user = None
        user_profile = None
        if '@' in identifier:
            try:
                user_profile = UserProfile.objects.get(email=identifier)
                username = user_profile.user.username
            except UserProfile.DoesNotExist:
                username = None
        else:
            username = identifier
            try:
                user_profile = UserProfile.objects.get(user__username=username)
            except UserProfile.DoesNotExist:
                pass

        # Check if the user exists and if the account is locked
        if user_profile:
            if user_profile.is_locked:
                print(f"Account locked for {identifier}")
                return JsonResponse({
                    'success': False,
                    'account_locked': True,
                    'message': (
                        "Your account is locked due to multiple failed login attempts. Please contact our support team at support@simskyeconomy.com to unlock your account."
                    )
                })

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        # If the username/email is valid (user exists), but the password is incorrect
        if (user_profile or user) and not user:
            # Increment the login attempts counter
            if user_profile:
                user_profile.login_attempts += 1
                print(f"Failed login attempt for {identifier}. Attempts: {user_profile.login_attempts}")
                if user_profile.login_attempts >= 5:
                    user_profile.is_locked = True

                    # Capture IP and geolocation
                    client_ip = self.get_client_ip(request)
                    location, latitude, longitude = self.get_geolocation(client_ip)

                    # Save IP and geolocation to the user model
                    user_profile.last_failed_ip = client_ip
                    user_profile.last_failed_location = location
                    user_profile.last_failed_latitude = latitude
                    user_profile.last_failed_longitude = longitude
                    user_profile.save()

                    print(f"Account locked for {identifier}. IP: {client_ip}, Location: {location}")

                    # Send email notification to the user
                    lockout_email_html = f"""
                    <html>
                        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                            <h2>Account Locked Notification</h2>
                            <p>Hello {username},</p>
                            <p>We have detected multiple failed login attempts on your SimSky Economy account.</p>
                            <p><strong>Username:</strong> {username}</p>
                            <p><strong>Email:</strong> {user_profile.email}</p>
                            <p><strong>Last Attempt IP:</strong> {client_ip}</p>
                            <p><strong>Last Attempt Location:</strong> {location}</p>
                            <p>For security reasons, your account has been temporarily locked. To regain access, please contact our support team at support@simskyeconomy.com.</p>
                            <p>If you did not attempt to log in, please secure your account immediately by resetting your password.</p>
                            <p>Best regards,<br>The SimSky Economy Team</p>
                        </body>
                    </html>
                    """
                    lockout_email_data = {
                        'email': user_profile.email,
                        'assunto': 'SimSky Economy: Your Account Has Been Locked',
                        'texto': lockout_email_html
                    }
                    response = requests.post(
                        'https://n8n.leonardolavourinha.com/webhook/1cd32f77-6428-491e-86ad-818f63524319',
                        json=lockout_email_data
                    )
                    if response.status_code != 200:
                        print(f"Failed to send lockout email to {user_profile.email}: {response.status_code} - {response.text}")

                    return JsonResponse({
                        'success': False,
                        'account_locked': True,
                        'message': (
                            "Your account is locked due to multiple failed login attempts. Please contact our support team at support@simskyeconomy.com to unlock your account."
                        )
                    })
                user_profile.save()

            return JsonResponse({
                'success': False,
                'email_not_verified': False,
                'message': 'Invalid username, email, or password.'
            })

        # If the login is successful (valid credentials)
        if user is not None:
            try:
                user_profile = UserProfile.objects.get(user=user)
                # Check if the email is verified
                if not user_profile.email_verified:
                    verification_url = reverse('resend_verification_email', args=[user.id])
                    print(f"Email not verified for user {user.username}. Verification URL: {verification_url}")
                    csrf_token = request.POST.get('csrfmiddlewaretoken')
                    return JsonResponse({
                        'success': False,
                        'email_not_verified': True,
                        'message': (
                            f"Your email is not verified. Please check your inbox for the verification email or "
                            f"<button class='btn btn-primary btn-sm' hx-post='{verification_url}' "
                            f"hx-target='#email-verification-modal-body' hx-swap='innerHTML' "
                            f"hx-headers='{{\"X-CSRFToken\": \"{csrf_token}\"}}'>Resend Verification Email</button>."
                        )
                    })
                # Reset login attempts counter after successful login
                user_profile.login_attempts = 0
                user_profile.save()
                login(request, user)
                print(f"User {user.username} logged in successfully")
                return redirect('userhome', user_id=user.id)
            except UserProfile.DoesNotExist:
                messages.error(request, 'User profile not found.')
                return render(request, self.template_name)
        else:
            print(f"Authentication failed for identifier: {identifier}")
            return JsonResponse({
                'success': False,
                'email_not_verified': False,
                'message': 'Invalid username, email, or password.'
            })

class ResendVerificationEmailView(View):
    def post(self, request, user_id):
        print(f"Resend verification email requested for user_id: {user_id}")
        try:
            user = User.objects.get(id=user_id)
            user_profile = UserProfile.objects.get(user=user)
            
            verification_token = EmailVerificationToken.objects.create(user=user)
            verification_link = request.build_absolute_uri(reverse('verify_email', args=[str(verification_token.token)]))
            print(f"Generated verification link: {verification_link}")
            
            verification_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <h2>Verify Your Email Address</h2>
                    <p>Hello {user.username},</p>
                    <p>Thank you for using SimSky Economy!</p>
                    <p>We noticed you need to verify your email address. Click the link below to complete this step:</p>
                    <p><a href="{verification_link}">{verification_link}</a></p>
                    <p>This link will expire in 30 minutes.</p>
                    <p>If you did not request this, please ignore this email.</p>
                    <p>Best regards,<br>The SimSky Economy Team</p>
                </body>
            </html>
            """
            verification_data = {
                'email': user_profile.email,
                'assunto': 'Please Verify Your SimSky Economy Email',
                'texto': verification_html
            }
            response = requests.post(
                'https://n8n.leonardolavourinha.com/webhook/1cd32f77-6428-491e-86ad-818f63524319',
                json=verification_data
            )
            
            if response.status_code != 200:
                print(f"Verification email webhook failed with status {response.status_code}: {response.text}")
                return HttpResponse("Failed to resend verification email. Please try again later.", status=500)
            
            print(f"Verification email sent successfully to {user_profile.email}")
            return HttpResponse("Verification email resent successfully! Please check your inbox.")
        except User.DoesNotExist:
            print(f"User with id {user_id} not found")
            return HttpResponse("User not found.", status=404)
        except UserProfile.DoesNotExist:
            print(f"User profile for user_id {user_id} not found")
            return HttpResponse("User profile not found.", status=404)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return HttpResponse(f"An error occurred: {str(e)}", status=500)

class PasswordResetView(View):
    def post(self, request):
        username_or_email = request.POST.get('username_or_email', '')
        user = None

        try:
            user = User.objects.get(username=username_or_email)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username_or_email)
            except User.DoesNotExist:
                pass

        if user:
            try:
                user_profile = UserProfile.objects.get(user=user)
                # Check if the account is locked
                if user_profile.is_locked:
                    return JsonResponse({
                        'success': False,
                        'account_locked': True,
                        'message': (
                            "Your account is locked due to multiple failed login attempts. Please contact our support team at support@simskyeconomy.com to unlock your account and proceed with password reset."
                        )
                    })

                # Proceed with password reset if the account is not locked
                reset_token = PasswordResetToken(user=user)
                reset_token.save()
                reset_link = request.build_absolute_uri(reverse('reset_password', args=[reset_token.token]))
                reset_text = f"""
                <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>Dear {user.username},</p>
                    <p>We received a request to reset your password for SimSky Economy.</p>
                    <p><strong>Username:</strong> {user.username}</p>
                    <p><strong>Email:</strong> {user_profile.email}</p>
                    <p>To reset your password, click the link below:</p>
                    <p><a href="{reset_link}">{reset_link}</a></p>
                    <p>This link will expire in 30 minutes.</p>
                    <p>If you did not request this, please ignore this message.</p>
                    <p>Best regards,<br>SimSky Economy Team</p>
                </body>
                </html>
                """
                payload = {
                    'username': user.username,
                    'email': user_profile.email,
                    'texto': reset_text,
                    'assunto': f"Dear {user.username}, SimSky Economy Account Password Reset"
                }
                response = requests.post(
                    'https://n8n.leonardolavourinha.com/webhook/1cd32f77-6428-491e-86ad-818f63524319',
                    json=payload
                )
                response.raise_for_status()
                return JsonResponse({'success': True})
            except UserProfile.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User profile not found.'})
            except requests.RequestException as e:
                return JsonResponse({'success': False, 'error': str(e)})

        return JsonResponse({'success': False, 'error': 'Username or email not found.'})
    
class ResetPasswordView(View):
    def get(self, request, token):
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            if reset_token.is_expired():
                reset_token.delete()
                return render(request, 'reset_password.html', {'error': 'This reset link has expired.'})
            return render(request, 'reset_password.html')
        except PasswordResetToken.DoesNotExist:
            return render(request, 'reset_password.html', {'error': 'Invalid reset link.'})

    def post(self, request, token):
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
            if reset_token.is_expired():
                reset_token.delete()
                return JsonResponse({'success': False, 'error': 'This reset link has expired.'})
            
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if new_password != confirm_password:
                return JsonResponse({'success': False, 'error': 'Passwords do not match.'})

            user = reset_token.user
            user.set_password(new_password)
            user.save()
            
            # Preparing the password reset confirmation email
            user_profile = UserProfile.objects.get(user=user)
            email_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <h2>Password Reset Successful, {user_profile.first_name}!</h2>
                    <p>Hello {user.username},</p>
                    <p>Your password for SimSky Economy has been successfully reset.</p>
                    <p><strong>Username:</strong> {user.username}</p>
                    <p><strong>Email:</strong> {user_profile.email}</p>
                    <p>You can now log in with your new password using your username: <strong>{user.username}</strong> or your email: <strong>{user_profile.email}</strong>.</p>
                    <p>If you did not request this change, please contact our support team immediately.</p>
                    <p>Best regards,<br>The SimSky Economy Team</p>
                </body>
            </html>
            """
            
            # JSON data for the webhook
            email_data = {
                'email': user_profile.email,
                'assunto': 'Your SimSky Economy Password Has Been Reset',
                'texto': email_html
            }
            
            # Sending the email to the webhook
            webhook_url = 'https://n8n.leonardolavourinha.com/webhook/1cd32f77-6428-491e-86ad-818f63524319'
            response = requests.post(webhook_url, json=email_data)
            
            # Checking if the webhook failed
            if response.status_code != 200:
                print(f"Webhook failed with status {response.status_code}: {response.text}")
            
            reset_token.delete()
            return JsonResponse({'success': True})
        except PasswordResetToken.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid reset link.'})
        except UserProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User profile not found.'})
        except requests.RequestException as e:
            return JsonResponse({'success': False, 'error': f'Failed to send confirmation email: {str(e)}'})