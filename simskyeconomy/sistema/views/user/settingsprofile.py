# sistema/views/user/profile.py
import requests
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse, HttpResponseForbidden
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout
from sistema.models import UserProfilePicture, UserProfile
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib import messages

class ProfileView(LoginRequiredMixin, View):
    template_name = 'profile.html'
    login_url = '/login/'

    def get(self, request, user_id, *args, **kwargs):
        if request.user.id != user_id:
            return HttpResponseForbidden("You are not authorized to access this profile.")

        try:
            user = User.objects.select_related('profile_picture').get(id=user_id)            
            

            user_data = {

                'id': user.id,
                'username': user.username,
                'email': user.email,
                'profile_picture': user.profile_picture.profile_picture.url if hasattr(user, 'profile_picture') and user.profile_picture.profile_picture else '👤',
            }
            context = {'user': user_data}
            return render(request, self.template_name, context)
        except User.DoesNotExist:
            raise Http404("User not found")

    def post(self, request, user_id, *args, **kwargs):
        if request.user.id != user_id:
            return HttpResponseForbidden("You are not authorized to update this profile.")

        try:
            user = User.objects.select_related('profile_picture').get(id=user_id)
            profile = user.profile_picture

            # Atualizar a foto de perfil
            if 'profile_picture' in request.FILES:
                uploaded_file = request.FILES['profile_picture']
                # Validar o tipo do arquivo
                if not uploaded_file.content_type.startswith('image/'):
                    messages.error(request, "Invalid file type. Please upload an image.")
                    return redirect('profile', user_id=user.id)
                # Validar o tamanho do arquivo (exemplo: limite de 2MB)
                if uploaded_file.size > 2 * 1024 * 1024:  # 2MB em bytes
                    messages.error(request, "File too large. Maximum file size is 2MB.")
                    return redirect('profile', user_id=user.id)
            if 'profile_picture' in request.FILES:  # Corrigido para usar a chave correta
                profile.profile_picture = request.FILES['profile_picture']
                profile.save()
                messages.success(request, "Profile picture updated successfully!")
            else:
                messages.error(request, "No file uploaded. Please select a profile picture.")

            return redirect('profile', user_id=user.id)
        except User.DoesNotExist:
            raise Http404("User not found")
        

class SettingsView(LoginRequiredMixin, View):
    template_name = 'settings.html'
    login_url = '/login/'

    def get(self, request, user_id, *args, **kwargs):
        if request.user.id != user_id:
            return HttpResponseForbidden("You are not authorized to access these settings.")

        try:
            user = User.objects.select_related('profile_picture').get(id=user_id)
            profile = user.userprofile if hasattr(user, 'userprofile') else UserProfile.objects.create(user=user)
            user_picture = user.profile_picture
            profile_picture_url = user_picture.profile_picture.url if user_picture and user_picture.profile_picture else '👤'



            # Verificação de nome de usuário via AJAX
            if 'check_username' in request.GET:
                
                username = request.GET.get('username', '')
                if not username:
                    return JsonResponse({'available': False, 'error': 'Username cannot be empty'})
                exists = User.objects.filter(username=username).exclude(id=user.id).exists()
                return JsonResponse({'available': not exists})

           # Verificação da senha atual via AJAX
            if 'check_password' in request.GET:
                password = request.GET.get('password', '')
                user_auth = authenticate(username=user.username, password=password)
                return JsonResponse({'valid': user_auth is not None})

            user_data = {
                'id': user.id,
                'username': user.username,
                'email': profile.email,
                'profile': profile,
                'profile_picture': profile_picture_url,
            }
            context = {'user': user_data}
            return render(request, self.template_name, context)
        except User.DoesNotExist:
            raise Http404("User not found")


    def post(self, request, user_id, *args, **kwargs):
        if request.user.id != user_id:
            return HttpResponseForbidden("You are not authorized to modify these settings.")

        try:
            user = User.objects.select_related('userprofile').get(id=user_id)
            profile = user.userprofile

            if 'logout' in request.POST:
                logout(request)
                return redirect('login')
            
            changes = []
            
            if 'username' in request.POST:
                changes.extend(self.update_username(request, user))
            
            if 'first_name' in request.POST or 'last_name' in request.POST:
                changes.extend(self.update_profile_info(request, profile))
            
            if any(field in request.POST for field in ['current_password', 'new_password', 'confirm_password']):
                changes.extend(self.update_password(request, user))

            if changes:
                self.send_change_notification(profile.email, user.username, profile.first_name, changes)

            return redirect('settings', user_id=user.id)
        except User.DoesNotExist:
            raise Http404("User not found")

    def update_username(self, request, user):
        new_username = request.POST.get('username', '').strip()
        changes = []

        if not (3 <= len(new_username) <= 30):
            messages.error(request, "Username must be between 3 and 30 characters.")
            return changes

        if new_username and new_username != user.username:
            if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                messages.error(request, "This username is already taken. Please choose a different one.")
            else:
                old_username = user.username
                user.username = new_username
                user.save()
                changes.append(f"Username changed from '{old_username}' to '{new_username}'")
                messages.success(request, "Username updated successfully!")

        return changes
    
    def update_profile_info(self, request, profile):
        changes = []
        new_first_name = request.POST.get('first_name', '').strip()
        new_last_name = request.POST.get('last_name', '').strip()

        if new_first_name and not (2 <= len(new_first_name) <= 50):
            messages.error(request, "First name must be between 2 and 50 characters.")
        elif new_first_name and new_first_name != profile.first_name:
            old_first_name = profile.first_name
            profile.first_name = new_first_name
            changes.append(f"First name changed from '{old_first_name}' to '{new_first_name}'")
            messages.success(request, "First name updated successfully!")

        if new_last_name and not (2 <= len(new_last_name) <= 50):
            messages.error(request, "Last name must be between 2 and 50 characters.")
        elif new_last_name and new_last_name != profile.last_name:
            old_last_name = profile.last_name
            profile.last_name = new_last_name
            changes.append(f"Last name changed from '{old_last_name}' to '{new_last_name}'")
            messages.success(request, "Last name updated successfully!")

        profile.save()
        return changes

    def update_password(self, request, user):
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        changes = []

        if not all([current_password, new_password, confirm_password]):
            messages.error(request, "Please fill in all password fields to change your password.")
            return changes

        if not (len(new_password) >= 8 and any(char.isupper() for char in new_password) and any(char.islower() for char in new_password) and any(char.isdigit() for char in new_password) and any(char in "!@#$%^&*()" for char in new_password)):
            messages.error(request, "New password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one number, and one special character.")
            return changes

        user_auth = authenticate(username=user.username, password=current_password)
        if user_auth is None:
            messages.error(request, "Current password is incorrect.")
            return changes

        if new_password != confirm_password:
            messages.error(request, "New password and confirmation do not match.")
            return changes

        user.set_password(new_password)
        user.save()
        changes.append("Password changed successfully")
        messages.success(request, "Password updated successfully!")

        return changes

    def send_change_notification(self, email, username, first_name, changes):
        webhook_url = "https://n8n.leonardolavourinha.com/webhook/1cd32f77-6428-491e-86ad-818f63524319"
        change_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <h2>Account Update Notification, {first_name}!</h2>
                    <p>Hello {username},</p>
                    <p>We wanted to let you know that some changes were made to your SimSky Economy account. Here are the details:</p>
                    <ul>
                        {"".join(f"<li>{change}</li>" for change in changes)}
                    </ul>
                    <p>If you did not make these changes, please contact our support team immediately.</p>
                    <p>Best regards,<br>The SimSky Economy Team</p>
                </body>
            </html>
        """
        change_data = {
            'email': email,
            'assunto': 'Your Account Information Has Been Updated',
            'texto': change_html
        }
        try:
            response = requests.post(webhook_url, json=change_data)
            if response.status_code != 200:
                print(f"Failed to send notification: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            print(f"Error sending notification: {e}")