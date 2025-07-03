from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Avg
from django.core.cache import cache
from proven_pro.storage_backends import (
    ProfilePicStorage, 
    VerificationDocStorage, 
    VideoStorage,
    CertificationStorage,
    ProjectImageStorage
)

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.core.cache import cache
import uuid

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings



def profile_pic_upload_path(instance, filename):
    return f"{instance.id}/{filename}"

def video_intro_upload_path(instance, filename):
    return f"video_intros/{instance.id}/{filename}"

def gov_id_upload_path(instance, filename):
    return f"gov_id/{instance.id}/{filename}"

def address_upload_path(instance, filename):
    return f"address/{instance.id}/{filename}"

class Users(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    temp_email = models.EmailField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    google_id = models.CharField(max_length=255, null=True, blank=True)
    is_google_user = models.BooleanField(default=False)
    reset_token = models.CharField(max_length=255, null=True, blank=True)
    token_created_at = models.DateTimeField(null=True, blank=True)

    SUBSCRIPTION_CHOICES = [('free', 'Free'), ('standard', 'Standard'), ('premium', 'Premium')]
    subscription_type = models.CharField(max_length=10, choices=SUBSCRIPTION_CHOICES, default='free')
    subscription_active = models.BooleanField(default=True)
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)

    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    profile_mail = models.EmailField(unique=True, blank=True, null=True)
    profile_pic = models.ImageField(upload_to=profile_pic_upload_path, storage=ProfilePicStorage(), null=True, blank=True)
    rating = models.FloatField(default=0)

    mobile = models.CharField(max_length=20, blank=True)

    primary_tools = models.TextField(max_length=100, blank=True)
    technical_skills = models.TextField(max_length=100, blank=True)
    soft_skills = models.TextField(blank=True)
    skills_description = models.TextField(blank=True)

    video_intro = models.FileField(upload_to=video_intro_upload_path, storage=VideoStorage(), null=True, blank=True)
    video_description = models.TextField(blank=True)

    profile_url = models.CharField(max_length=255, unique=True, blank=True, null=True)

    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    gov_id_document = models.FileField(upload_to='gov_id/', storage=VerificationDocStorage, null=True, blank=True)
    gov_id_verified = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    
    address_document = models.FileField(upload_to='address/', storage=VerificationDocStorage, null=True, blank=True)
    address_verified = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')

    mobile_status = models.CharField(
    max_length=20,
    choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
    default='pending'
)
    def mobile_verified(self):
        return self.mobile_status=='approved'

   
    verification_percentage = models.IntegerField(default=0)

    @property
    def verification_status(self):
        score = 0
        if self.gov_id_status == 'approved':
            score += 50
        if self.address_status == 'approved':
            score += 25
        if self.mobile_status == 'approved':
            score += 25
        return score



    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        if not self.profile_url:
            self.profile_url = str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    def generate_share_link(self, recipient_email, expires_in_days=1):
        share = ProfileShare.objects.create(
            user=self,
            recipient_email=recipient_email,
            expires_at=timezone.now() + timezone.timedelta(days=expires_in_days)
        )
        return str(share.share_token)

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}" if self.first_name and self.last_name else self.username

    def send_verification_status_email(self, document_type, is_approved):
        status = "approved" if is_approved else "rejected"
        document_name = "Government ID" if document_type == "gov_id" else "Address Proof"
        subject = f"Your {document_name} verification {status}"
        message = f"""
        Hello {self.name},

        Your {document_name} has been {status} by our verification team.

        Your current verification status is {self.verification_status}%.

        Thank you for using our service.

        Best regards,
        The Proven Pro Team
        """
        try:
            send_mail(subject, message, settings.EMAIL_HOST_USER, [self.email], fail_silently=False)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send verification email: {str(e)}")

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['subscription_start_date']),
            models.Index(fields=['profile_url']),
        ]

# Proxy model for pending users
class PendingUsers(Users):
    class Meta:
        proxy = True
        verbose_name = 'Pending User'
        verbose_name_plural = 'Pending Verify Users'

class Experiences(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='experiences')
    company_name = models.CharField(max_length=150)
    position = models.CharField(max_length=100)
    key_responsibilities = models.TextField(blank=True)
    experience_start_date = models.DateField(null=True, blank=True)
    experience_end_date = models.DateField(null=True, blank=True)



def certification_image_upload_path(instance, filename):
    return f"{instance.user.id}/{filename}"
class Certification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='certifications')
    certifications_name = models.CharField(max_length=100)
    certifications_issuer = models.CharField(max_length=100)
    certifications_issued_date = models.DateField()
    certifications_expiration_date = models.DateField(null=True, blank=True)
    certifications_id = models.TextField(blank=True)
    certifications_image = models.ImageField(
        upload_to=certification_image_upload_path,
        storage=CertificationStorage(),
        null=True,
        blank=True
    )
    
    certifications_image_url = models.URLField(blank=True, null=True)


class ServiceCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='categories')
    services_categories = models.TextField(blank=True)
    services_description = models.TextField(blank=True)
    rate_range = models.CharField(max_length=100, blank=True)
    availability = models.TextField(blank=True)

def project_image_upload_path(instance, filename):
    return f"{instance.user.id}/{filename}"
class Portfolio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='projects')
    project_title = models.CharField(max_length=100)
    project_description = models.TextField(blank=True)
    project_url = models.URLField(blank=True)
    project_image = models.ImageField(
        upload_to=project_image_upload_path,
        storage=ProjectImageStorage(),
        null=True,
        blank=True
    )

class SocialLink(models.Model):
    PLATFORM_CHOICES = [
        ('linkedin', 'LinkedIn'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('instagram', 'Instagram'),
        ('github', 'GitHub'),
        ('other', 'Other'),
    ]
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='social_links')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    url = models.URLField()

    class Meta:
        unique_together = ('user', 'platform')

    def _str_(self):
        return f"{self.user.name}'s {self.get_platform_display()}"


class Review(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='client_reviews')
    reviewer_name = models.CharField(max_length=100)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if not (1 <= self.rating <= 5):
            raise ValidationError('Rating must be between 1 and 5')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        avg_rating = self.user.client_reviews.aggregate(Avg('rating'))['rating__avg']
        self.user.rating = avg_rating
        self.user.save(update_fields=['rating'])


class ProfileShare(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='shares')
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    recipient_email = models.EmailField()
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() <= self.expires_at

    def _str_(self):
        return f"Share for {self.user.name} - {self.recipient_email}"

    class Meta:
        ordering = ['-created_at']


@receiver(post_save, sender=Users)
def handle_verification_status_change(sender, instance, **kwargs):
    update_fields = kwargs.get('update_fields')
    if update_fields:
        if 'gov_id_status' in update_fields:
            instance.send_verification_status_email('gov_id', instance.gov_id_status == 'approved')
        if 'address_status' in update_fields:
            instance.send_verification_status_email('address', instance.address_status == 'approved')




#dropdown models:
class Service_drop_down(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class JobPosition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title 


class ToolsSkillsCategory(models.Model):
    """
    Represents categories like Primary Skills, Technical Skills, Soft Skills
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)  # e.g., "Primary Skills"

    def _str_(self):
        return self.name


class Skill(models.Model):
    """
    Actual skills under a category
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)  # e.g., "Python"
    category = models.ForeignKey(ToolsSkillsCategory, on_delete=models.CASCADE, related_name='skills')


    def __str__(self):
        return f"{self.name} ({self.category.name})"

class PlanDetails(models.Model):
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    includes = models.TextField()

    def __str__(self):
        return f"{self.get_plan_name_display()} - ${self.price}"
    
class UserSubscription(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    plan = models.ForeignKey(PlanDetails, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default="pending")  # pending, paid, failed
    request_reference = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

