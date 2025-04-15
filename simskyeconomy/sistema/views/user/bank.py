# sistema/views/user/bank.py
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from sistema.models import UserProfilePicture

class BankView(LoginRequiredMixin, View):
    template_name = 'bank.html'
    login_url = '/login/'

    def get(self, request, user_id, *args, **kwargs):
        if request.user.id != user_id:
            return redirect('bank', user_id=request.user.id)

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