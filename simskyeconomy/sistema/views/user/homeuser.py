# sistema/views/user/homeuser.py
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.contrib.auth import logout
from sistema.models import UserProfilePicture

class Homeuser(LoginRequiredMixin, View):
    template_name = 'user.html'
    login_url = '/login/'

    def get(self, request, user_id, *args, **kwargs):
        if request.user.id != user_id:
            return redirect('userhome', user_id=request.user.id)

        try:
            user = User.objects.get(id=user_id)
            profile, created = UserProfilePicture.objects.get_or_create(user=user)
            user_data = {
                'id': user.id,
                'username': user.username,
                'profile_picture': profile.profile_picture.url if profile.profile_picture else None,
            }
            context = {'user': user_data}
            return render(request, self.template_name, context)
        except User.DoesNotExist:
            raise Http404("User not found")

    def post(self, request, user_id, *args, **kwargs):
        if request.user.id != user_id:
            return redirect('userhome', user_id=request.user.id)

        if 'logout' in request.POST:
            logout(request)
            return redirect('login')

        return self.get(request, user_id, *args, **kwargs)