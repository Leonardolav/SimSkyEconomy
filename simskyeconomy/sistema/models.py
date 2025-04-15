from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import secrets
import uuid

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=13, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(6)[:13]
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=30)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.username} - {self.token}"

class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_expired(self):
        return (timezone.now() - self.created_at).total_seconds() > 1800  # 30 minutes expiration

    def __str__(self):
        return f"Token for {self.user.username}"

class Currency(models.Model):
    name = models.CharField(max_length=20)
    code = models.CharField(max_length=3)

    def __str__(self):
        return self.name

class ReputationLevel(models.Model):
    min_score = models.IntegerField()
    reputation_grade = models.CharField(max_length=2)

    def __str__(self):
        return self.reputation_grade
    
class ReputationType(models.Model):
    type = models.CharField(max_length=50)
    description = models.CharField(max_length=100)
    score = models.IntegerField()

    def __str__(self):
        return self.type

class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_profile')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    registration_date = models.DateField()
    reputation_level = models.ForeignKey('ReputationLevel', on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    cash_balance = models.DecimalField(max_digits=13, decimal_places=2, default=0.00)
    first_access = models.BooleanField()
    email_verified = models.BooleanField()
    login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    preferred_currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    last_failed_ip = models.CharField(max_length=45, blank=True, null=True)  # Supports IPv4 and IPv6
    last_failed_location = models.CharField(max_length=255, blank=True, null=True)
    last_failed_latitude = models.FloatField(blank=True, null=True)
    last_failed_longitude = models.FloatField(blank=True, null=True)

    def __str__(self):
        return str(self.user)
    

class UserProfilePicture(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile_picture')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile picture"

    
class Reputation(models.Model):
    reputation_id = models.CharField(max_length=13)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    reputation_type = models.ForeignKey(ReputationType, on_delete=models.CASCADE)  
    score_date = models.DateField()
    reason = models.CharField(max_length=50)

    def __str__(self):
        return self.reputation_id
    
class UserEarnings(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=13, decimal_places=2, default=0.00)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)  
    description = models.CharField(max_length=50)
    date = models.DateField()

    def __str__(self):
        return f"{self.user.user.username} - {self.amount}"
    
class UserExpenses(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=13, decimal_places=2, default=0.00)  
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    description = models.CharField(max_length=50)
    date = models.DateField()

    def __str__(self):
        return f"{self.user.user.username} - {self.amount}"
    
class License(models.Model):
    name = models.CharField(max_length=100)
    category_code = models.CharField(max_length=5)
    price = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    requires_obligations = models.BooleanField()
    required_licenses = models.CharField(max_length=300)
    required_level = models.ForeignKey(ReputationLevel, on_delete=models.CASCADE)
    validity_period = models.IntegerField()

    def __str__(self):
        return self.name

class TheoreticalTest(models.Model):
    question = models.CharField(max_length=200)
    option_a = models.CharField(max_length=150)
    option_b = models.CharField(max_length=150)
    option_c = models.CharField(max_length=150)
    option_d = models.CharField(max_length=150)
    correct_answer = models.CharField(max_length=1)
    license = models.ForeignKey(License, on_delete=models.CASCADE)

    def __str__(self):
        return self.question
    
class PracticalTest(models.Model):
    procedure = models.CharField(max_length=50)
    min_altitude = models.IntegerField()
    max_altitude = models.IntegerField()
    max_speed = models.IntegerField()
    restrictions = models.CharField(max_length=100)
    obligations = models.CharField(max_length=100)
    license = models.ForeignKey(License, on_delete=models.CASCADE)

    def __str__(self):
        return self.procedure
    
class UserLicense(models.Model):
    license = models.ForeignKey(License, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    issue_date = models.DateField()
    first_issue_date = models.DateField()
    expiration_date = models.DateField()

    def __str__(self):
        return str(self.license)