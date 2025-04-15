# sistema/views/user/profile.py
import requests
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, logout
from sistema.models import UserProfilePicture, UserProfile
from django.contrib import messages

class ProfileView(LoginRequiredMixin, View):
    template_name = 'profile.html'
    login_url = '/login/'

    def get(self, request, user_id, *args, **kwargs):
        if request.user.id != user_id:
            return redirect('profile', user_id=request.user.id)

        try:
            user = User.objects.get(id=user_id)
            # Certifique-se de que o perfil existe
            profile, created = UserProfilePicture.objects.get_or_create(user=user)
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'profile_picture': profile.profile_picture.url if profile.profile_picture else None,
            }
            context = {'user': user_data}
            return render(request, self.template_name, context)
        except User.DoesNotExist:
            raise Http404("User not found")

    def post(self, request, user_id, *args, **kwargs):
        if request.user.id != user_id:
            return redirect('profile', user_id=request.user.id)

        try:
            user = User.objects.get(id=user_id)
            profile, created = UserProfilePicture.objects.get_or_create(user=user)

            # Atualizar a foto de perfil
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
            return redirect('settings', user_id=request.user.id)

        try:
            user = User.objects.get(id=user_id)
            profile, created = UserProfile.objects.get_or_create(user=user)
            user_picture, created = UserProfilePicture.objects.get_or_create(user=user)

            # Verificação de nome de usuário via AJAX
            if 'check_username' in request.GET:
                username = request.GET.get('username', '').strip()
                if username:
                    exists = User.objects.filter(username=username).exclude(id=user.id).exists()
                    return JsonResponse({'available': not exists})
                return JsonResponse({'available': False, 'error': 'Username cannot be empty'})

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
                'profile_picture': user_picture.profile_picture.url if user_picture.profile_picture else None,
            }
            context = {'user': user_data}
            return render(request, self.template_name, context)
        except User.DoesNotExist:
            raise Http404("User not found")

    def post(self, request, user_id, *args, **kwargs):
        if request.user.id != user_id:
            return redirect('settings', user_id=request.user.id)

        try:
            user = User.objects.get(id=user_id)
            profile = UserProfile.objects.get(user=user)

            # Verificar se o botão de logout foi clicado
            if 'logout' in request.POST:
                logout(request)
                return redirect('login')

            # Lista para rastrear mudanças
            changes = []

            # Atualizar username (apenas se alterado)
            if 'username' in request.POST:
                new_username = request.POST['username'].strip()
                if new_username and new_username != user.username:
                    if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                        messages.error(request, "This username is already taken. Please choose a different one.")
                    else:
                        old_username = user.username
                        user.username = new_username
                        user.save()
                        changes.append(f"Username changed from '{old_username}' to '{new_username}'")
                        messages.success(request, "Username updated successfully!")

            # Atualizar first_name (apenas se alterado)
            if 'first_name' in request.POST:
                new_first_name = request.POST['first_name'].strip()
                if new_first_name and new_first_name != profile.first_name:
                    old_first_name = profile.first_name
                    profile.first_name = new_first_name
                    profile.save()
                    changes.append(f"First name changed from '{old_first_name}' to '{new_first_name}'")
                    messages.success(request, "First name updated successfully!")

            # Atualizar last_name (apenas se alterado)
            if 'last_name' in request.POST:
                new_last_name = request.POST['last_name'].strip()
                if new_last_name and new_last_name != profile.last_name:
                    old_last_name = profile.last_name
                    profile.last_name = new_last_name
                    profile.save()
                    changes.append(f"Last name changed from '{old_last_name}' to '{new_last_name}'")
                    messages.success(request, "Last name updated successfully!")

            # Alterar senha (apenas se os campos de senha forem preenchidos)
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if current_password or new_password or confirm_password:
                if not (current_password and new_password and confirm_password):
                    messages.error(request, "Please fill in all password fields to change your password.")
                else:
                    # Verificar a senha atual
                    user_auth = authenticate(username=user.username, password=current_password)
                    if user_auth is not None:
                        if new_password == confirm_password:
                            user.set_password(new_password)
                            user.save()
                            changes.append("Password changed successfully")
                            messages.success(request, "Password updated successfully!")
                        else:
                            messages.error(request, "New password and confirmation do not match.")
                    else:
                        messages.error(request, "Current password is incorrect.")

            # Enviar e-mail via webhook se houver mudanças
            if changes:
                self.send_change_notification(profile.email, user.username, profile.first_name, changes)

            return redirect('settings', user_id=user.id)
        except User.DoesNotExist:
            raise Http404("User not found")

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