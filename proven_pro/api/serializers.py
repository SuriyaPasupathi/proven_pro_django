from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import SocialLink, Review, ProfileShare, Experience, Certification, ServiceCategory, Project
import re

Users = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Users
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = Users.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


# ----------------------
# ✅ Forgot Password
# ----------------------
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


# ----------------------
# ✅ Reset Password
# ----------------------
class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])


class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ('id', 'username', 'email')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ('id', 'username', 'email', 'first_name', 'last_name')


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ('id', 'platform', 'url')


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ('id', 'user', 'reviewer_name', 'rating', 'comment', 'created_at')
        # If you want to hide the user field in responses but allow it in creation:
        extra_kwargs = {
            'user': {'write_only': True}
        }


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ('id', 'company_name', 'position', 'key_responsibilities', 'experience_start_date', 'experience_end_date')
        # Remove 'user' from fields to avoid circular reference


class CertificationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Certification
        fields = ('id', 'certifications_name', 'certifications_issuer', 'certifications_issued_date', 'certifications_expiration_date', 'certifications_id', 
                  'certifications_image_url')
        # Remove 'user' from fields to avoid circular reference


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ('id', 'services_categories', 'services_description', 'rate_range', 'availability')
        # Remove 'user' from fields to avoid circular reference


class ProjectSerializer(serializers.ModelSerializer):

    
    class Meta:
        model = Project
        fields = ('id', 'project_title', 'project_description', 'project_url',)
        # Remove 'user' from fields to avoid circular reference


class UserProfileSerializer(serializers.ModelSerializer):
    # Include all related data with nested serializers
    social_links = SocialLinkSerializer(many=True, read_only=True)
    client_reviews = ReviewSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    categories = ServiceCategorySerializer(many=True, read_only=True)
    projects = ProjectSerializer(many=True, read_only=True)
    
    # Fields for nested creation
    linkedin = serializers.URLField(write_only=True, required=False, allow_blank=True)
    facebook = serializers.URLField(write_only=True, required=False, allow_blank=True)
    twitter = serializers.URLField(write_only=True, required=False, allow_blank=True)
    
    # Experience fields for direct creation
    company_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    position = serializers.CharField(write_only=True, required=False, allow_blank=True)
    experience_start_date = serializers.DateField(write_only=True, required=False)
    experience_end_date = serializers.DateField(write_only=True, required=False)
    key_responsibilities = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    # Project fields for direct creation
    project_title = serializers.CharField(write_only=True, required=False, allow_blank=True)
    project_description = serializers.CharField(write_only=True, required=False, allow_blank=True)
    project_url = serializers.URLField(write_only=True, required=False, allow_blank=True)
    project_image = serializers.ImageField(write_only=True, required=False, allow_null=True)
    
    # Certification fields for direct creation
    certifications_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    certifications_issuer = serializers.CharField(write_only=True, required=False, allow_blank=True)
    certifications_issued_date = serializers.DateField(write_only=True, required=False)
    certifications_expiration_date = serializers.DateField(write_only=True, required=False, allow_null=True)
    certifications_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    certifications_image = serializers.ImageField(write_only=True, required=False)
    
    # Service category fields for direct access
    services_categories = serializers.CharField(write_only=True, required=False, allow_blank=True)
    services_description = serializers.CharField(write_only=True, required=False, allow_blank=True)
    rate_range = serializers.CharField(write_only=True, required=False, allow_blank=True)
    availability = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    verification_status = serializers.IntegerField(read_only=True)
    
    # Add these fields as write-only to avoid serialization issues
    profile_pic = serializers.ImageField(write_only=True, required=False)
    video_intro = serializers.FileField(write_only=True, required=False)
    
    # Add URL fields for reading the file URLs
    profile_pic_url = serializers.SerializerMethodField(read_only=True)
    video_intro_url = serializers.SerializerMethodField(read_only=True)
    
    def get_profile_pic_url(self, obj):
        if obj.profile_pic:
            return obj.profile_pic.url
        return None
    
    def get_video_intro_url(self, obj):
        if obj.video_intro:
            return obj.video_intro.url
        return None
    
    class Meta:
        model = Users
        fields = (
            'id', 'username', 'email', 'subscription_type', 'subscription_active',
            'subscription_start_date', 'subscription_end_date',
            
            # Profile fields
            'first_name', 'last_name', 'bio', 
            'profile_pic', 'profile_pic_url', 'rating', 'profile_url', 'profile_mail',
            'mobile', 
            
            # Tools & skills
            'primary_tools', 'technical_skills', 'soft_skills', 'skills_description',
            
            # Related models
            'social_links', 'client_reviews', 'experiences', 'certifications',
            'categories', 'projects',
            'video_intro', 'video_intro_url', 'video_description', 
            
            # Write-only fields for social links
            'linkedin', 'facebook', 'twitter',
            
            # Write-only fields for experience
            'company_name', 'position', 'experience_start_date', 'experience_end_date', 'key_responsibilities',
            
            # Write-only fields for project
            'project_title', 'project_description', 'project_url', 'project_image',
            
            # Write-only fields for certification
            'certifications_name', 'certifications_issuer', 'certifications_issued_date', 
            'certifications_expiration_date', 'certifications_id', 'certifications_image',
            
            # Write-only fields for service categories
            'services_categories', 'services_description', 'rate_range', 'availability',
            
            # Verification fields
            'gov_id_document', 'gov_id_verified',
            'address_document', 'address_verified',
            'mobile_verified', 'verification_status',
        )
    
    def create(self, validated_data):
        # Extract social links data
        linkedin = validated_data.pop('linkedin', None)
        facebook = validated_data.pop('facebook', None)
        twitter = validated_data.pop('twitter', None)
        
        # Create user
        user = Users.objects.create(**validated_data)
        
        # Create social links if provided
        social_links = []
        if linkedin:
            social_links.append(SocialLink(user=user, platform='linkedin', url=linkedin))
        if facebook:
            social_links.append(SocialLink(user=user, platform='facebook', url=facebook))
        if twitter:
            social_links.append(SocialLink(user=user, platform='twitter', url=twitter))
        
        if social_links:
            SocialLink.objects.bulk_create(social_links)
        
        return user
    
    def update(self, instance, validated_data):
        # Extract social links data
        linkedin = validated_data.pop('linkedin', None)
        facebook = validated_data.pop('facebook', None)
        twitter = validated_data.pop('twitter', None)
        
        # Extract experience data
        company_name = validated_data.pop('company_name', None)
        position = validated_data.pop('position', None)
        experience_start_date = validated_data.pop('experience_start_date', None)
        experience_end_date = validated_data.pop('experience_end_date', None)
        key_responsibilities = validated_data.pop('key_responsibilities', None)
        
        # Extract project data
        project_title = validated_data.pop('project_title', None)
        project_description = validated_data.pop('project_description', None)
        project_url = validated_data.pop('project_url', None)
        project_image = validated_data.pop('project_image', None)
        
        # Extract certification data
        certifications_name = validated_data.pop('certifications_name', None)
        certifications_issuer = validated_data.pop('certifications_issuer', None)
        certifications_issued_date = validated_data.pop('certifications_issued_date', None)
        certifications_expiration_date = validated_data.pop('certifications_expiration_date', None)
        certifications_id = validated_data.pop('certifications_id', None)
        certifications_image = validated_data.pop('certifications_image', None)
        
        # Extract service category data
        services_categories = validated_data.pop('services_categories', None)
        services_description = validated_data.pop('services_description', None)
        rate_range = validated_data.pop('rate_range', None)
        availability = validated_data.pop('availability', None)
        
        # Update user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update social links
        if linkedin is not None:
            SocialLink.objects.update_or_create(
                user=instance, platform='linkedin',
                defaults={'url': linkedin}
            )
        if facebook is not None:
            SocialLink.objects.update_or_create(
                user=instance, platform='facebook',
                defaults={'url': facebook}
            )
        if twitter is not None:
            SocialLink.objects.update_or_create(
                user=instance, platform='twitter',
                defaults={'url': twitter}
            )
        
        # Create experience if all required fields are provided
        if all([company_name, position, experience_start_date, experience_end_date]):
            Experience.objects.create(
                user=instance,
                company_name=company_name,
                position=position,
                experience_start_date=experience_start_date,
                experience_end_date=experience_end_date,
                key_responsibilities=key_responsibilities or ''
            )
        
        # Create project if title is provided
        if project_title:
            project = Project.objects.create(
                user=instance,
                project_title=project_title,
                project_description=project_description or '',
                project_url=project_url or ''
            )
            # Only set project_image if it's a valid file object
            if project_image and hasattr(project_image, 'name'):
                project.project_image = project_image
                project.save()
        
        # Create certification if name and issuer are provided
        if certifications_name and certifications_issuer and certifications_issued_date:
            certification = Certification.objects.create(
                user=instance,
                certifications_name=certifications_name,
                certifications_issuer=certifications_issuer,
                certifications_issued_date=certifications_issued_date,
                certifications_expiration_date=certifications_expiration_date,
                certifications_id=certifications_id or ''
            )
            if certifications_image:
                certification.certifications_image = certifications_image
                certification.save()
        
        # Update service category if any of the fields are provided
        if any(field is not None for field in [services_categories, services_description, rate_range, availability]):
            ServiceCategory.objects.update_or_create(
                user=instance,
                defaults={
                    'services_categories': services_categories if services_categories is not None else '',
                    'services_description': services_description if services_description is not None else '',
                    'rate_range': rate_range if rate_range is not None else '',
                    'availability': availability if availability is not None else ''
                }
            )
        
        return instance


class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset and setting new password
    """
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    
    def validate_new_password(self, value):
        """
        Validate that the new password meets complexity requirements:
        - At least 8 characters
        - Contains a number
        - Contains a letter
        - Contains a special character
        """
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
            
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one number.")
            
        if not re.search(r'[a-zA-Z]', value):
            raise serializers.ValidationError("Password must contain at least one letter.")
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
            
        return value


class ProfileShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileShare
        fields = ['share_token', 'recipient_email', 'expires_at']
        read_only_fields = ['share_token', 'expires_at']


class PublicProfileSerializer(serializers.ModelSerializer):
    experiences = ExperienceSerializer(many=True, read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    projects = ProjectSerializer(many=True, read_only=True)
    profile_pic_url = serializers.SerializerMethodField(read_only=True)
    video_intro_url = serializers.SerializerMethodField(read_only=True)
    
    def get_profile_pic_url(self, obj):
        if obj.profile_pic:
            return obj.profile_pic.url
        return None
    
    def get_video_intro_url(self, obj):
        if obj.video_intro:
            return obj.video_intro.url
        return None
    
    class Meta:
        model = Users
        fields = [
            'id',
            'first_name',
            'last_name',
            'profile_pic_url',
            'rating',
            'subscription_type',
            'email',
            'mobile',
            'bio',
            'services_description',
            'rate_range',
            'availability',
            'primary_tools',
            'technical_skills',
            'soft_skills',
            'skills_description',
            'video_intro_url',
            'video_description',
            'experiences',
            'certifications',
            'projects'
        ]



