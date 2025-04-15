from django.contrib import admin
from .models import (
    Currency,
    UserProfile,
    ReputationLevel,
    ReputationType,
    Reputation,
    UserEarnings,
    UserExpenses,
    License,
    TheoreticalTest,
    PracticalTest,
    UserLicense,
)

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'first_name', 'last_name', 'email','cash_balance', 'registration_date', 'reputation_level', 'score', 'first_access',
        'email_verified', 'preferred_currency', 'is_locked', 'last_failed_ip', 'last_failed_location',
        'last_failed_latitude', 'last_failed_longitude'
    )
    list_filter = ('first_access', 'registration_date', 'reputation_level', 'preferred_currency')
    search_fields = ('first_name', 'last_name', 'email', 'user__username', 'is_locked')

@admin.register(ReputationLevel)
class ReputationLevelAdmin(admin.ModelAdmin):
    list_display = ('reputation_grade', 'min_score')
    search_fields = ('reputation_grade',)

@admin.register(ReputationType)
class ReputationTypeAdmin(admin.ModelAdmin):
    list_display = ('type', 'description', 'score')
    search_fields = ('type', 'description')

@admin.register(Reputation)
class ReputationAdmin(admin.ModelAdmin):
    list_display = ('reputation_id', 'user', 'reputation_type', 'score_date', 'reason')
    list_filter = ('score_date',)
    search_fields = ('reputation_id', 'reason', 'user__user__username')


@admin.register(UserEarnings)
class UserEarningsAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'currency', 'description', 'date')
    list_filter = ('date', 'currency', 'user__preferred_currency')
    search_fields = ('description', 'user__user__username')

@admin.register(UserExpenses)
class UserExpensesAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'currency', 'description', 'date')
    list_filter = ('date', 'currency', 'user__preferred_currency')
    search_fields = ('description', 'user__user__username')

@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_code', 'price', 'requires_obligations', 'required_level', 'validity_period')
    list_filter = ('requires_obligations', 'required_level')
    search_fields = ('name', 'category_code', 'required_licenses')

@admin.register(TheoreticalTest)
class TheoreticalTestAdmin(admin.ModelAdmin):
    list_display = ('question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'license')
    list_filter = ('license',)
    search_fields = ('question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer')

@admin.register(PracticalTest)
class PracticalTestAdmin(admin.ModelAdmin):
    list_display = ('procedure', 'min_altitude', 'max_altitude', 'max_speed', 'license')
    list_filter = ('license',)
    search_fields = ('procedure', 'restrictions', 'obligations')

@admin.register(UserLicense)
class UserLicenseAdmin(admin.ModelAdmin):
    list_display = ('license', 'user', 'issue_date', 'first_issue_date', 'expiration_date')
    list_filter = ('issue_date', 'expiration_date')
    search_fields = ('license__name', 'user__user__username')