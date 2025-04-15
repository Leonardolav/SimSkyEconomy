from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect, render
from django.db.models import Prefetch
from django.views import View


class Homeuser(LoginRequiredMixin, View):
    template_name = 'user.html'
    login_url = '/login/'

    def get(self, request, user_id, *args, **kwargs):
        if request.user.id != user_id:            
            raise PermissionDenied("You do not have permission to access this page.")

        try:            
            user = User.objects.filter(id=user_id).prefetch_related(Prefetch('profile_picture')).first()
            if user is None:
                raise Http404("User not found")

            try:
                profile_picture = user.profile_picture.profile_picture.url
            except AttributeError:
                profile_picture = '👤'           

            user_data = {
                'id': user.id,
                'username': user.username,
                'profile_picture': profile_picture,
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