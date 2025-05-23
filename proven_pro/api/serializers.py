from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Review, Experience, Certification, ServiceCategory, Portfolio, SocialLink, ProfileShare
import re

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])


class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
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
        fields = [
            'id',
            'company_name',
            'position',
            'key_responsibilities',
            'experience_start_date',
            'experience_end_date'
        ]



class CertificationSerializer(serializers.ModelSerializer):
    certifications_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Certification
        fields = [
            'id',
            'certifications_name',
            'certifications_issuer',
            'certifications_issued_date',
            'certifications_expiration_date',
            'certifications_id',
            'certifications_image',
            'certifications_image_url'
        ]

    def get_certifications_image_url(self, obj):
        if obj.certifications_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.certifications_image.url).replace('/api/', '/')
            return obj.certifications_image.url
        return obj.certifications_image_url



class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = [
            'id',
            'services_categories',
            'services_description',
            'rate_range',
            'availability'
        ]


class PortfolioSerializer(serializers.ModelSerializer):
    project_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Portfolio
        fields = ['id', 'project_title', 'project_description', 'project_url', 'project_image', 'project_image_url']
    
    def get_project_image_url(self, obj):
        if obj.project_image:
            return self.context['request'].build_absolute_uri(obj.project_image.url)
        return None


class UserProfileSerializer(serializers.ModelSerializer):
    profile_pic_url = serializers.SerializerMethodField()
    video_intro_url = serializers.SerializerMethodField()
    portfolios = PortfolioSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    service_categories = ServiceCategorySerializer(many=True, read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        exclude = ['password', 'last_login', 'is_superuser', 'user_permissions', 'groups', 'is_staff', 'is_active', 'date_joined']
        read_only_fields = ['id', 'email', 'profile_pic_url', 'video_intro_url']

    def get_profile_pic_url(self, obj):
        if obj.profile_pic:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_pic.url).replace('/api/', '/')
            return obj.profile_pic.url
        return None

    def get_video_intro_url(self, obj):
        if obj.video_intro:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video_intro.url).replace('/api/', '/')
            return obj.video_intro.url
        return None

    def update(self, instance, validated_data):
        # Handle project data
        if 'project_title' in validated_data:
            project_data = {
                'project_title': validated_data.pop('project_title', ''),
                'project_description': validated_data.pop('project_description', ''),
                'project_url': validated_data.pop('project_url', '')
            }
            
            # Handle project image if it exists in the context
            request = self.context.get('request')
            if request and request.FILES and 'project_image' in request.FILES:
                project_data['project_image'] = request.FILES['project_image']
            
            # Clear existing projects and create new one
            instance.projects.all().delete()
            portfolio.objects.create(user=instance, **project_data)
        
        # Handle experience data
        if 'company_name' in validated_data:
            experience_data = {
                'company_name': validated_data.pop('company_name', ''),
                'position': validated_data.pop('position', ''),
                'key_responsibilities': validated_data.pop('key_responsibilities', ''),
                'experience_start_date': validated_data.pop('experience_start_date', None),
                'experience_end_date': validated_data.pop('experience_end_date', None)
            }
            
            # Clear existing experiences and create new one
            instance.experiences.all().delete()
            Experience.objects.create(user=instance, **experience_data)
        
        # Handle service categories data - removed from here, will be handled in the view
        
        # Handle certification data
        if 'certifications_name' in validated_data:
            certification_data = {
                'certifications_name': validated_data.pop('certifications_name', ''),
                'certifications_issuer': validated_data.pop('certifications_issuer', ''),
                'certifications_issued_date': validated_data.pop('certifications_issued_date', None),
                'certifications_expiration_date': validated_data.pop('certifications_expiration_date', None),
                'certifications_id': validated_data.pop('certifications_id', '')
            }
            
            # Handle certification image if it exists in the context
            request = self.context.get('request')
            if request and request.FILES and 'certifications_image' in request.FILES:
                certification_data['certifications_image'] = request.FILES['certifications_image']
            
            # Clear existing certifications and create new one
            instance.certifications.all().delete()
            Certification.objects.create(user=instance, **certification_data)
        
        # Update user instance fields
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
    projects = PortfolioSerializer(many=True, read_only=True)
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
        model = User
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
