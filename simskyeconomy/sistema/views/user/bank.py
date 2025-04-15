# sistema/views/user/bank.py
from django.views import View
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseForbidden
from sistema.models import UserProfilePicture

class NoProfilePicture(Exception):
    pass
from django.db.models import Prefetch

class BankView(LoginRequiredMixin, View):
    template_name = 'bank.html'
    login_url = '/login/'

    def get(self, request, user_id, *args, **kwargs):
        if request.user.id != user_id:
            return HttpResponseForbidden("You do not have permission to access this bank information.")

        try:
            user = User.objects.filter(id=user_id).select_related('profile_picture').first()
            if user is None:
                raise Http404("User not found")
            if user.profile_picture is None:
                raise NoProfilePicture
            try:
                profile_picture = user.profile_picture.profile_picture.url
            except NoProfilePicture:
                profile_picture = '👤'            
            user_data = {
                'id': user.id,
                'username': user.username,
                'profile_picture': profile_picture,
            }
            context = {'user': user_data}
            return render(request, self.template_name, context)        except NoProfilePicture:            profile_picture = '👤'            user_data = {                'id': user.id,                'username': user.username,                'profile_picture': profile_picture,            }            context = {'user': user_data}            return render(request, self.template_name, context)        except User.DoesNotExist:            raise Http404("User not found")        except Exception:            raise Http404("Error")