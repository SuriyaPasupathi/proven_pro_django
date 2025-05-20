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
        fields = ('id', 'company_name', 'position', 'key_responsibilities', 'start_date', 'end_date')


class CertificationSerializer(serializers.ModelSerializer):
    certificate_image_url = serializers.SerializerMethodField(read_only=True)
    
    def get_certificate_image_url(self, obj):
        if obj.certificate_image:
            return obj.certificate_image.url
        return None
    
    class Meta:
        model = Certification
        fields = ('id', 'name', 'issuer', 'issued_date', 'expiration_date', 'credential_id', 
                  'certificate_image', 'certificate_image_url')
        extra_kwargs = {
            'certificate_image': {'write_only': True}
        }


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ('id', 'name')


class ProjectSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)
    
    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None
    
    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'url', 'image', 'image_url')
        extra_kwargs = {
            'image': {'write_only': True}
        }


class UserProfileSerializer(serializers.ModelSerializer):
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
            
            'services_description', 'rate_range', 'availability',
            
            # Tools & skills
            'primary_tools', 'technical_skills', 'soft_skills', 'skills_description',
            
            # Video
            'video_intro', 'video_intro_url', 'video_description',
            
            # Related models
            'social_links', 'client_reviews', 'experiences', 'certifications', 
            'categories', 'projects',
            
            # Write-only fields for social links
            'linkedin', 'facebook', 'twitter',
            
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



