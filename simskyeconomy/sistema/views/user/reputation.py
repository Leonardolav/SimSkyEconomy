from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseForbidden
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from sistema.models import User, UserProfile, Reputation, ReputationLevel, UserProfilePicture  # Importar o novo modelo

class ReputationView(LoginRequiredMixin, View):
    template_name = 'reputation.html'
    login_url = '/login/'
    items_per_page = 30

    def get(self, request, user_id, *args, **kwargs):
        if request.user.id != user_id:            
            return HttpResponseForbidden("You are not authorized to view this page.")

        try:
            user = User.objects.select_related('userprofile', 'profile_picture').get(id=user_id)
            profile = user.userprofile
            user_picture = user.userprofilepicture.profile_picture if hasattr(user, 'userprofilepicture') else None
            reputation_data_dict = self.get_reputation_data(request, profile)            
            context = self.prepare_context(user, user_picture, reputation_data_dict['total_score'], reputation_data_dict['level'], reputation_data_dict['progress_percent'],
                                            reputation_data_dict['current_min_score'], reputation_data_dict['next_min_score'], reputation_data_dict['score_30_days'],
                                            reputation_data_dict['score_60_days'], reputation_data_dict['score_90_days'], reputation_data_dict['reputations'], request.GET.get('period', 'all'))
            return render(request, self.template_name, context)
        except User.DoesNotExist:
            raise Http404("User not found")
        except UserProfile.DoesNotExist:
            raise Http404("User profile not found")
    
    def get_reputation_data(self, request, profile):
        period = request.GET.get('period', 'all')
        today = timezone.now().date()
        reputations = Reputation.objects.filter(user=profile).select_related('reputation_type').order_by('-score_date')
        
        if period != 'all':
            days = int(period)
            start_date = today - timedelta(days=days)
            reputations = reputations.filter(score_date__gte=start_date)
        
        paginator = Paginator(reputations, self.items_per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        total_score = profile.score
        current_level_obj = ReputationLevel.objects.filter(min_score__lte=total_score).order_by('-min_score').first()
        
        if not current_level_obj:
            current_level_obj = ReputationLevel.objects.order_by('min_score').first()
        
        current_level = current_level_obj.reputation_grade
        current_min_score = current_level_obj.min_score
        next_level_obj = ReputationLevel.objects.filter(min_score__gt=total_score).order_by('min_score').first()
        progress_percent = self.calculate_progress_percent(total_score, current_min_score, next_level_obj)
        
        if profile.reputation_level != current_level_obj:
            profile.reputation_level = current_level_obj
            profile.save(update_fields=['reputation_level'])
        
        score_30_days = sum(r.reputation_type.score for r in reputations.filter(score_date__gte=today - timedelta(days=30)))
        score_60_days = sum(r.reputation_type.score for r in reputations.filter(score_date__gte=today - timedelta(days=60)))
        score_90_days = sum(r.reputation_type.score for r in reputations.filter(score_date__gte=today - timedelta(days=90)))
        
        return {
            'total_score': total_score,
            'level': current_level,
            'progress_percent': f"{progress_percent:.1f}",
            'current_min_score': current_min_score,
            'next_min_score': next_level_obj.min_score if next_level_obj else None,
            'score_30_days': score_30_days,
            'score_60_days': score_60_days,
            'score_90_days': score_90_days,
            'reputations': page_obj,
        }
    
    def calculate_progress_percent(self, total_score, current_min_score, next_level_obj):
        if next_level_obj:
            next_min_score = next_level_obj.min_score
            score_range = next_min_score - current_min_score
            if score_range > 0:
                progress_percent = ((total_score - current_min_score) / score_range) * 100
                return min(max(round(progress_percent, 1), 0.0), 100.0)
        return 100.0
    
    def prepare_context(self, user, user_picture, total_score, current_level, progress_percent_str, current_min_score, next_level_obj, score_30_days, score_60_days, score_90_days, page_obj, period):
        reputation_data = {
            'total_score': total_score,
            'level': current_level,
            'progress_percent': progress_percent_str,
            'current_min_score': current_min_score,
            'next_min_score': next_level_obj.min_score if next_level_obj else None,            
            'score_30_days': score_30_days,
            'score_60_days': score_60_days,
            'score_90_days': score_90_days,
            'reputations': page_obj
        }
        
        return {
            'user': {'id': user.id, 'username': user.username, 'profile_picture': user_picture.url if user_picture else '👤'},
            'reputation_data': reputation_data,
            'page_obj': page_obj,
            'selected_period': period,
            }