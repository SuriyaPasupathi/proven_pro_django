from django.db import models    
from django.contrib.auth.models import AbstractUser as AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

class Users(AbstractUser):
    # Base user fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    google_id = models.CharField(max_length=255, null=True, blank=True)
    is_google_user = models.BooleanField(default=False)
    reset_token = models.CharField(max_length=255, null=True, blank=True)
    token_created_at = models.DateTimeField(null=True, blank=True)
    
    # Subscription fields
    SUBSCRIPTION_CHOICES = [
        ('free', 'Free'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    subscription_type = models.CharField(max_length=10, choices=SUBSCRIPTION_CHOICES, default='free')
    subscription_active = models.BooleanField(default=True)
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    
    # Profile fields
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='user_profiles_pic/', null=True, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    job_specialization = models.CharField(max_length=100, blank=True)
    rating = models.FloatField(default=0)
    
    # Standard tier fields
    mobile = models.CharField(max_length=20, blank=True)
    services = models.TextField(blank=True)
    experiences = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    tools = models.TextField(blank=True)
    languages = models.TextField(blank=True)
    categories = models.TextField(blank=True)
    
    # Premium tier fields
    education = models.TextField(blank=True)
    certifications = models.TextField(blank=True)
    licenses = models.TextField(blank=True)
    portfolio = models.TextField(blank=True)
    video_intro = models.FileField(upload_to='videos/', null=True, blank=True)
    
    # URL for profile sharing
    profile_url = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    # Verification fields
    gov_id_document = models.FileField(upload_to='verification/gov_id/', null=True, blank=True)
    gov_id_verified = models.BooleanField(default=False)
    address_document = models.FileField(upload_to='verification/address/', null=True, blank=True)
    address_verified = models.BooleanField(default=False)
    mobile_verified = models.BooleanField(default=False)
    verification_percentage = models.IntegerField(default=0)
    
    @property
    def verification_status(self):
        """Calculate verification percentage based on verified documents"""
        percentage = 0
        if self.gov_id_verified:
            percentage += 50
        if self.address_verified:
            percentage += 25
        if self.mobile_verified:
            percentage += 25
        
        # Update the stored percentage
        if self.verification_percentage != percentage:
            self.verification_percentage = percentage
            self.save(update_fields=['verification_percentage'])
        
        return percentage
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def save(self, *args, **kwargs):
        # Generate a unique profile URL if not provided
        if not self.profile_url:
            self.profile_url = str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)
    
    def generate_share_link(self, recipient_email, expires_in_days=7):
        share = ProfileShare.objects.create(
            user=self,
            recipient_email=recipient_email,
            expires_at=timezone.now() + timezone.timedelta(days=expires_in_days)
        )
        return str(share.share_token)
    
    @property
    def name(self):
        """Return the user's full name or username"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    # Add a method to send verification status email
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
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [self.email],
                fail_silently=False,
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send verification email: {str(e)}")


class SocialLink(models.Model):
    """Separate model for social media links to keep the data structure clean"""
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
    
    def __str__(self):
        return f"{self.user.name}'s {self.get_platform_display()}"


class Review(models.Model):
    """Model for client reviews"""
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='client_reviews')
    reviewer_name = models.CharField(max_length=100)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        if self.rating < 1 or self.rating > 5:
            raise ValidationError('Rating must be between 1 and 5')
        
    def save(self, *args, **kwargs):
        self.full_clean()  # This will run validators and clean method
        super().save(*args, **kwargs)
        
        # Update the average rating on the user
        user = self.user
        reviews = user.client_reviews.all()
        if reviews:
            user.rating = sum(review.rating for review in reviews) / reviews.count()
            user.save(update_fields=['rating'])


class ProfileShare(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='shares')
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    recipient_email = models.EmailField()
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def is_valid(self):
        return timezone.now() <= self.expires_at
    
    def __str__(self):
        return f"Share for {self.user.name} - {self.recipient_email}"
    
    class Meta:
        ordering = ['-created_at']

# Add signals to detect changes in verification status
@receiver(post_save, sender=Users)
def handle_verification_status_change(sender, instance, **kwargs):
    # This is a simple implementation. For production, you might want to use a more
    # sophisticated approach to detect actual changes in verification fields
    if kwargs.get('update_fields') and any(field in kwargs['update_fields'] for field in 
                                          ['gov_id_verified', 'address_verified']):
        if 'gov_id_verified' in kwargs['update_fields']:
            instance.send_verification_status_email('gov_id', instance.gov_id_verified)
        if 'address_verified' in kwargs['update_fields']:
            instance.send_verification_status_email('address', instance.address_verified)



