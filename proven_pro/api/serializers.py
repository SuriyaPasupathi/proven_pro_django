from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import SocialLink, Review, ProfileShare,Experiences, Certification, ServiceCategory, Portfolio
import re
import json
import logging

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


class work_experiences_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Experiences 
        fields = '__all__'
        # Remove 'user' from fields to avoid circular reference


class CertificationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Certification
        fields = ('id', 'certifications_name', 'certifications_issuer', 'certifications_issued_date', 'certifications_expiration_date', 'certifications_id', 
                  'certifications_image_url')
        # Remove 'user' from fields  to avoid circular reference


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ('id', 'services_categories', 'services_description', 'rate_range', 'availability')
        # Remove 'user' from fields to avoid circular reference


class PortfolioSerializer(serializers.ModelSerializer):

    
    class Meta:
        model = Portfolio
        fields = '__all__'
        # Remove 'user' from fields to avoid circular reference


class UserProfileSerializer(serializers.ModelSerializer):
    # Related data
    social_links = SocialLinkSerializer(many=True, read_only=True)
    client_reviews = ReviewSerializer(many=True, read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    categories = ServiceCategorySerializer(many=True, read_only=True)
    projects = PortfolioSerializer(many=True, read_only=True)
    experiences = work_experiences_Serializer(many=True, read_only=True)

    # File URL fields
    profile_pic_url = serializers.SerializerMethodField(read_only=True)
    video_intro_url = serializers.SerializerMethodField(read_only=True)

    # Write-only fields for nested creation
    work_experiences = serializers.CharField(write_only=True, required=False, allow_blank=True)
    linkedin = serializers.URLField(write_only=True, required=False, allow_blank=True)
    facebook = serializers.URLField(write_only=True, required=False, allow_blank=True)
    twitter = serializers.URLField(write_only=True, required=False, allow_blank=True)

    # Experience direct fields
    company_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    position = serializers.CharField(write_only=True, required=False, allow_blank=True)
    experience_start_date = serializers.DateField(write_only=True, required=False)
    experience_end_date = serializers.DateField(write_only=True, required=False)
    key_responsibilities = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # Project fields
    project_title = serializers.CharField(write_only=True, required=False, allow_blank=True)
    project_description = serializers.CharField(write_only=True, required=False, allow_blank=True)
    project_url = serializers.URLField(write_only=True, required=False, allow_blank=True)
    project_image = serializers.ImageField(write_only=True, required=False, allow_null=True)

    # Certification fields
    certifications_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    certifications_issuer = serializers.CharField(write_only=True, required=False, allow_blank=True)
    certifications_issued_date = serializers.DateField(write_only=True, required=False)
    certifications_expiration_date = serializers.DateField(write_only=True, required=False, allow_null=True)
    certifications_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    certifications_image = serializers.ImageField(write_only=True, required=False)

    # Service Category fields
    services_categories = serializers.CharField(write_only=True, required=False, allow_blank=True)
    services_description = serializers.CharField(write_only=True, required=False, allow_blank=True)
    rate_range = serializers.CharField(write_only=True, required=False, allow_blank=True)
    availability = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # Media
    profile_pic = serializers.ImageField(write_only=True, required=False)
    video_intro = serializers.FileField(write_only=True, required=False)

    # Read-only
    verification_status = serializers.IntegerField(read_only=True)

    class Meta:
        model = Users
        fields = (
            'id', 'username', 'email', 'subscription_type', 'subscription_active',
            'subscription_start_date', 'subscription_end_date',
            'first_name', 'last_name', 'bio', 'profile_pic', 'profile_pic_url',
            'rating', 'profile_url', 'profile_mail', 'mobile',
            'primary_tools', 'technical_skills', 'soft_skills', 'skills_description',
            'social_links', 'client_reviews', 'experiences', 'certifications',
            'categories', 'projects', 'video_intro', 'video_intro_url', 'video_description',
            'linkedin', 'facebook', 'twitter',
            'work_experiences', 'company_name', 'position', 'experience_start_date',
            'experience_end_date', 'key_responsibilities',
            'project_title', 'project_description', 'project_url', 'project_image',
            'certifications_name', 'certifications_issuer', 'certifications_issued_date',
            'certifications_expiration_date', 'certifications_id', 'certifications_image',
            'services_categories', 'services_description', 'rate_range', 'availability',
            'gov_id_document', 'gov_id_verified', 'address_document', 'address_verified',
            'mobile_verified', 'verification_status',
        )

    def get_profile_pic_url(self, obj):
        return obj.profile_pic.url if obj.profile_pic else None

    def get_video_intro_url(self, obj):
        return obj.video_intro.url if obj.video_intro else None

    def validate(self, data):
        self.work_experiences_data = self.initial_data.get('work_experiences')
        self.portfolio_data = self.initial_data.get('portfolio')
        self.certifications_data = self.initial_data.get('certifications')
        self.categories_data = self.initial_data.get('categories')
        self.social_links_data = self.initial_data.get('social_links')

        self.project_images = {
            key.split('_')[-1]: self.initial_data[key]
            for key in self.initial_data if key.startswith('project_image_')
        }

        print(f"Extracted work_experiences: {self.work_experiences_data}")
        print(f"Extracted portfolio: {self.portfolio_data}")
        print(f"Extracted project images: {self.project_images.keys()}")
        print(f"extracted categories:{self.categories_data}")

        return data

    def update(self, instance, validated_data):
        # Work experiences
        if self.work_experiences_data:
            try:
                experiences_list = json.loads(self.work_experiences_data)
                for exp in experiences_list:
                    Experiences.objects.create(
                        user=instance,
                        company_name=exp.get('company_name', ''),
                        position=exp.get('position', ''),
                        experience_start_date=exp.get('experience_start_date'),
                        experience_end_date=exp.get('experience_end_date'),
                        key_responsibilities=exp.get('key_responsibilities', '')
                    )
            except Exception as e:
                print(f"Error processing experiences: {e}")

        # Portfolio
        if self.portfolio_data:
            try:
                projects_list = json.loads(self.portfolio_data)
                for i, proj in enumerate(projects_list):
                    Portfolio.objects.create(
                        user=instance,
                        project_title=proj.get('project_title', ''),
                        project_description=proj.get('project_description', ''),
                        project_url=proj.get('project_url', ''),
                        project_image=self.project_images.get(str(i))
                    )
            except Exception as e:
                print(f"Error processing portfolio: {e}")
                import traceback
                print(traceback.format_exc())

        # Certification
        if validated_data.get('certifications_name') and validated_data.get('certifications_issuer') and validated_data.get('certifications_issued_date'):
            try:
                certification = Certification.objects.create(
                    user=instance,
                    certifications_name=validated_data.pop('certifications_name'),
                    certifications_issuer=validated_data.pop('certifications_issuer'),
                    certifications_issued_date=validated_data.pop('certifications_issued_date'),
                    certifications_expiration_date=validated_data.pop('certifications_expiration_date', None),
                    certifications_id=validated_data.pop('certifications_id', ''),
                    certifications_image=validated_data.pop('certifications_image', None)
                )
                image_url = self.initial_data.get('certifications_image_url')
                if image_url and image_url.startswith('http'):
                    certification.certifications_image_url = image_url
                    certification.save()
            except Exception as e:
                print(f"Error creating certification: {e}")
                logging.error(f"Error creating certification: {e}")

        # Service categories
        categories_data = getattr(self, 'categories_data', [])
        print("📦 Raw categories_data:", categories_data)

        # Convert from string to list if needed
        if isinstance(categories_data, str):
            try:
                categories_data = json.loads(categories_data)
                print("✅ Parsed categories_data:", categories_data)
            except json.JSONDecodeError as e:
                print("❌ JSON decode error:", e)
                categories_data = []

        if isinstance(categories_data, list):
            for idx, category in enumerate(categories_data):
                print(f"🔍 Processing category {idx + 1}: {category}")
                if isinstance(category, dict):
                    try:
                        sc = ServiceCategory.objects.create(
                            user=instance,
                            services_categories=category.get('services_categories', ''),
                            services_description=category.get('services_description', ''),
                            rate_range=category.get('rate_range', ''),
                            availability=category.get('availability', '')
                        )
                        print(f"✅ Saved ServiceCategory ID: {sc.id}")
                    except Exception as e:
                        print(f"❌ Failed to save category: {e}")
                else:
                    print("⚠️ Skipped non-dict item.")
        else:
            print("⚠️ categories_data is not a list even after parsing.")

        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()

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
    experiences = work_experiences_Serializer(many=True, read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    projects = PortfolioSerializer(many=True, read_only=True)
    categories = ServiceCategorySerializer(many=True, read_only=True)
    # Add fields for reading the file URLs
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
            'work_experiences',
            'certifications',
            'projects'
        ]


