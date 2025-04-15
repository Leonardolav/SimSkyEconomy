# sistema/views/user/homeuser.py
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import redirect, render
from django.views import View
from sistema.models import UserProfilePicture, UserProfile

class Homeuser(LoginRequiredMixin, View):
    template_name = 'user.html'
    login_url = '/login/'

    def get(self, request, user_id, *args, **kwargs):
        if request.user.id != user_id:
            raise PermissionDenied("You do not have permission to access this page.")

        try:
            user = User.objects.prefetch_related(
                Prefetch(
                    "userprofilepicture_set",
                    queryset=UserProfilePicture.objects.all(),
                    to_attr="profile_pictures"
                )
            ).only("id", "username").get(id=user_id)
            profile_picture = user.profile_pictures[0].profile_picture.url if user.profile_pictures else None
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
            raise PermissionDenied("You do not have permission to perform this action.")

        if 'logout' in request.POST:
            logout(request)
            return redirect('login')

        return self.get(request, user_id, *args, **kwargs)