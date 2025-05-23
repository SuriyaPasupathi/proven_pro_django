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
        fields = ('id', 'company_name', 'position', 'key_responsibilities', 'experience_start_date', 'experience_end_date')


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = (
            'id', 'certifications_name', 'certifications_issuer', 'certifications_issued_date',
            'certifications_expiration_date', 'certifications_id', 'certifications_image_url'
        )


class ServicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = ('id', 'services_categories', 'services_description', 'rate_range', 'availability')


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ('id', 'project_title', 'project_description', 'project_url')


class UserProfileSerializer(serializers.ModelSerializer):
    social_links = SocialLinkSerializer(many=True, read_only=True)
    client_reviews = ReviewSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    services = ServicesSerializer(many=True, read_only=True)
    portfolio = PortfolioSerializer(many=True, read_only=True)

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
            'mobile_verified', 'verification_status'
        )

    def update(self, instance, validated_data):
        # Handle social links
        linkedin = validated_data.pop('linkedin', None)
        facebook = validated_data.pop('facebook', None)
        twitter = validated_data.pop('twitter', None)

        # Handle experience
        company_name = validated_data.pop('company_name', None)
        position = validated_data.pop('position', None)
        experience_start_date = validated_data.pop('experience_start_date', None)
        experience_end_date = validated_data.pop('experience_end_date', None)
        key_responsibilities = validated_data.pop('key_responsibilities', None)

        # Handle portfolio
        project_title = validated_data.pop('project_title', None)
        project_description = validated_data.pop('project_description', None)
        project_url = validated_data.pop('project_url', None)
        project_image = validated_data.pop('project_image', None)
        project_image_url = validated_data.pop('project_image_url', None)

        # Handle certification
        certifications_name = validated_data.pop('certifications_name', None)
        certifications_issuer = validated_data.pop('certifications_issuer', None)
        certifications_issued_date = validated_data.pop('certifications_issued_date', None)
        certifications_expiration_date = validated_data.pop('certifications_expiration_date', None)
        certifications_id = validated_data.pop('certifications_id', None)
        certifications_image = validated_data.pop('certifications_image', None)

        # Handle service category
        services_categories = validated_data.pop('services_categories', None)
        services_description = validated_data.pop('services_description', None)
        rate_range = validated_data.pop('rate_range', None)
        availability = validated_data.pop('availability', None)

        # Update basic user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update social links
        if linkedin is not None:
            SocialLink.objects.update_or_create(user=instance, platform='linkedin', defaults={'url': linkedin})
        if facebook is not None:
            SocialLink.objects.update_or_create(user=instance, platform='facebook', defaults={'url': facebook})
        if twitter is not None:
            SocialLink.objects.update_or_create(user=instance, platform='twitter', defaults={'url': twitter})

        # Create experience if all required fields are present
        if all([company_name, position, experience_start_date, experience_end_date]):
            Experience.objects.create(
                user=instance,
                company_name=company_name,
                position=position,
                experience_start_date=experience_start_date,
                experience_end_date=experience_end_date,
                key_responsibilities=key_responsibilities or ''
            )

        # Create portfolio item if title is provided
        if project_title:
            portfolio_data = {
                'user': instance,
                'project_title': project_title,
                'project_description': project_description or '',
                'project_url': project_url or ''
            }
            
            if project_image:
                portfolio_data['project_image'] = project_image
            
            Portfolio.objects.create(**portfolio_data)

        # Create certification if required fields are present
        if certifications_name and certifications_issuer and certifications_issued_date:
            certification_data = {
                'user': instance,
                'certifications_name': certifications_name,
                'certifications_issuer': certifications_issuer,
                'certifications_issued_date': certifications_issued_date,
                'certifications_expiration_date': certifications_expiration_date,
                'certifications_id': certifications_id or ''
            }
            
            if certifications_image:
                certification_data['certifications_image'] = certifications_image
                
            Certification.objects.create(**certification_data)

        # Create service if any field is provided
        if any([services_categories, services_description, rate_range, availability]):
            Services.objects.create(
                user=instance,
                services_categories=services_categories or '',
                services_description=services_description or '',
                rate_range=rate_range or '',
                availability=availability or ''
            )

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
