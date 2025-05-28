from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import SocialLink, Review, ProfileShare, Experience, Certification, Services, Portfolio
import re

Users = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Users
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        return Users.objects.create_user(**validated_data)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


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
        extra_kwargs = {
            'user': {'write_only': True}
        }


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = '__all__'


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = '__all__'


class ServicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = '__all__'


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = '__all__'


class UserProfileSerializer(serializers.ModelSerializer):
    # Nested serializers for reading data
    experiences = ExperienceSerializer(many=True, read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    services = ServicesSerializer(many=True, read_only=True)
    portfolio = PortfolioSerializer(many=True, read_only=True)

    # Write-only fields for creating/updating data
    experience = serializers.DictField(write_only=True, required=False)
    portfolio = serializers.DictField(write_only=True, required=False)
    certification = serializers.DictField(write_only=True, required=False)
    service = serializers.DictField(write_only=True, required=False)

    # Social links
    linkedin = serializers.URLField(write_only=True, required=False, allow_blank=True)
    facebook = serializers.URLField(write_only=True, required=False, allow_blank=True)
    twitter = serializers.URLField(write_only=True, required=False, allow_blank=True)

    # Experience
    company_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    position = serializers.CharField(write_only=True, required=False, allow_blank=True)
    experience_start_date = serializers.DateField(write_only=True, required=False)
    experience_end_date = serializers.DateField(write_only=True, required=False)
    key_responsibilities = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # Project
    project_title = serializers.CharField(write_only=True, required=False, allow_blank=True)
    project_description = serializers.CharField(write_only=True, required=False, allow_blank=True)
    project_url = serializers.URLField(write_only=True, required=False, allow_blank=True)
    project_image = serializers.ImageField(write_only=True, required=False, allow_null=True)
    project_image_url = serializers.URLField(write_only=True, required=False, allow_blank=True)

    # Certification
    certifications_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    certifications_issuer = serializers.CharField(write_only=True, required=False, allow_blank=True)
    certifications_issued_date = serializers.DateField(write_only=True, required=False)
    certifications_expiration_date = serializers.DateField(write_only=True, required=False, allow_null=True)
    certifications_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    certifications_image = serializers.ImageField(write_only=True, required=False)

    # Service Category
    services_categories = serializers.CharField(write_only=True, required=False, allow_blank=True)
    services_description = serializers.CharField(write_only=True, required=False, allow_blank=True)
    rate_range = serializers.CharField(write_only=True, required=False, allow_blank=True)
    availability = serializers.CharField(write_only=True, required=False, allow_blank=True)

    verification_status = serializers.IntegerField(read_only=True)

    profile_pic = serializers.ImageField(write_only=True, required=False)
    video_intro = serializers.FileField(write_only=True, required=False)

    profile_pic_url = serializers.SerializerMethodField(read_only=True)
    video_intro_url = serializers.SerializerMethodField(read_only=True)

    def get_profile_pic_url(self, obj):
        return obj.profile_pic.url if obj.profile_pic else None

    def get_video_intro_url(self, obj):
        return obj.video_intro.url if obj.video_intro else None

    class Meta:
        model = Users
        fields = (
            'id', 'username', 'email', 'subscription_type', 'subscription_active',
            'subscription_start_date', 'subscription_end_date', 'first_name', 'last_name', 'bio',
            'profile_pic', 'profile_pic_url', 'rating', 'profile_url', 'profile_mail', 'mobile',
            'primary_tools', 'technical_skills', 'soft_skills', 'skills_description',
            'social_links', 'client_reviews', 'experiences', 'certifications',
            'services', 'portfolio',
            'video_intro', 'video_intro_url', 'video_description',
            'linkedin', 'facebook', 'twitter',
            'company_name', 'position', 'experience_start_date', 'experience_end_date', 'key_responsibilities',
            'project_title', 'project_description', 'project_url', 'project_image', 'project_image_url',
            'certifications_name', 'certifications_issuer', 'certifications_issued_date',
            'certifications_expiration_date', 'certifications_id', 'certifications_image',
            'services_categories', 'services_description', 'rate_range', 'availability',
            'gov_id_document', 'gov_id_verified', 'address_document', 'address_verified',
            'mobile_verified', 'verification_status',
            'experience', 'portfolio', 'certification', 'service'
        )

    def update(self, instance, validated_data):
        # Handle experience data
        if 'experience' in validated_data:
            experience_data = validated_data.pop('experience')
            Experience.objects.create(user=instance, **experience_data)

        # Handle portfolio data
        if 'portfolio' in validated_data:
            portfolio_data = validated_data.pop('portfolio')
            Portfolio.objects.create(user=instance, **portfolio_data)

        # Handle certification data
        if 'certification' in validated_data:
            certification_data = validated_data.pop('certification')
            Certification.objects.create(user=instance, **certification_data)

        # Handle service data
        if 'service' in validated_data:
            service_data = validated_data.pop('service')
            Services.objects.create(user=instance, **service_data)

        # Update basic user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one number.")
        if not re.search(r'[a-zA-Z]', value):
            raise serializers.ValidationError("Password must contain at least one letter.")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', value):
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
    portfolio = PortfolioSerializer(many=True, read_only=True)
    profile_pic_url = serializers.SerializerMethodField(read_only=True)
    video_intro_url = serializers.SerializerMethodField(read_only=True)

    def get_profile_pic_url(self, obj):
        return obj.profile_pic.url if obj.profile_pic else None

    def get_video_intro_url(self, obj):
        return obj.video_intro.url if obj.video_intro else None

    class Meta:
        model = Users
        fields = [
            'id', 'first_name', 'last_name', 'profile_pic_url', 'rating', 'subscription_type',
            'email', 'mobile', 'bio', 'services_description', 'rate_range', 'availability',
            'primary_tools', 'technical_skills', 'soft_skills', 'skills_description',
            'video_intro_url', 'video_description', 'experiences', 'certifications', 'portfolio'
        ]
