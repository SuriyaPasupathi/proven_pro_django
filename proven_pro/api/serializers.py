from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import SocialLink, Review, ProfileShare,Experiences, Certification, ServiceCategory, Portfolio,JobPosition,Service_drop_down,Skill,ToolsSkillsCategory
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



# Forgot Password
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

# Reset Password
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
                  'certifications_image_url','certifications_image')
        # Remove 'user' from fields  to avoid circular reference


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ('id', 'services_categories', 'services_description', 'rate_range', 'availability')
        # Remove 'user' from fields to avoid circular reference


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ['id','user','project_title','project_description','project_url','project_image']
        # Remove 'user' from fields to avoid circular reference

#Drop Down Serilizers
class JobPositionserializers(serializers.ModelSerializer):
      class Meta:
        model = JobPosition
        fields = ['id', 'title']

class Skills_serializers(serializers.ModelSerializer):
    class Meta :
        model = Skill
        fields = '__all__'

class Tools_Skills_serializers(serializers.ModelSerializer):
    
    class Meta:
        model = ToolsSkillsCategory
        fields = '__all__'
    skills = Skills_serializers(many=True)

class  Service_drop_down_serializers(serializers.ModelSerializer):
    class Meta :
        model = Service_drop_down
        fields = '__all__'

#User profile Serilizers
class UserProfileSerializer(serializers.ModelSerializer):
    # Related nested fields
    social_links = SocialLinkSerializer(many=True, read_only=True)
    client_reviews = ReviewSerializer(many=True, read_only=True)
    work_experiences = work_experiences_Serializer(many=True, read_only=True, source='experiences')
    certifications = CertificationSerializer(many=True, read_only=True)
    categories = ServiceCategorySerializer(many=True, read_only=True)
    portfolio = PortfolioSerializer(many=True, read_only=True, source='projects')

    # Write-only direct create fields
    work_experiences_data = serializers.CharField(write_only=True, required=False, allow_blank=True)
    linkedin = serializers.URLField(write_only=True, required=False, allow_blank=True)
    facebook = serializers.URLField(write_only=True, required=False, allow_blank=True)
    twitter = serializers.URLField(write_only=True, required=False, allow_blank=True)
    
    # Experience fields
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

    # Service category
    services_categories = serializers.CharField(write_only=True, required=False, allow_blank=True)
    services_description = serializers.CharField(write_only=True, required=False, allow_blank=True)
    rate_range = serializers.CharField(write_only=True, required=False, allow_blank=True)
    availability = serializers.CharField(write_only=True, required=False, allow_blank=True)

    # Media Fields
    profile_pic = serializers.ImageField(write_only=True, required=False)
    video_intro = serializers.FileField(write_only=True, required=False)
    profile_pic_url = serializers.SerializerMethodField(read_only=True)
    video_intro_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Users
        fields = ('id', 'username', 'email', 'subscription_type', 'subscription_active',
            'subscription_start_date', 'subscription_end_date',
            'first_name', 'last_name', 'bio',
            'primary_tools', 'technical_skills', 'soft_skills', 'skills_description',
            'profile_pic', 'profile_pic_url', 'rating', 'profile_url', 'profile_mail', 'mobile',
            'social_links', 'client_reviews', 'work_experiences', 'certifications', 'categories', 'portfolio',
            'video_intro', 'video_intro_url', 'video_description',
            'linkedin', 'facebook', 'twitter',
            'work_experiences_data', 'company_name', 'position', 'experience_start_date', 
            'experience_end_date', 'key_responsibilities',
            'project_title', 'project_description', 'project_url', 'project_image',
            'certifications_name', 'certifications_issuer', 'certifications_issued_date', 
            'certifications_expiration_date', 'certifications_id', 'certifications_image',
            'services_categories', 'services_description', 'rate_range', 'availability',
            'gov_id_document', 'gov_id_verified', 'address_document', 'address_verified',
            'mobile_verified', 'verification_status')

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
        self.certification_images = {
            key.split('_')[-1]: self.initial_data[key]
            for key in self.initial_data if key.startswith('certifications_image_')
        }

        return data

    def update(self, instance, validated_data):
        for field in ['first_name', 'last_name', 'bio', 'primary_tools', 'technical_skills',
                      'soft_skills', 'skills_description', 'video_description', 'mobile']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        if 'profile_pic' in validated_data:
            instance.profile_pic = validated_data['profile_pic']
        if 'video_intro' in validated_data:
            instance.video_intro = validated_data['video_intro']

            instance.save()

        # Handle Experiences
        if self.work_experiences_data:
            try:
                for exp in json.loads(self.work_experiences_data):
                    exp_id = exp.get("id")
                    if exp_id:
                        Experiences.objects.filter(id=exp_id, user=instance).update(
                            company_name=exp.get('company_name', ''),
                            position=exp.get('position', ''),
                            experience_start_date=exp.get('experience_start_date'),
                            experience_end_date=exp.get('experience_end_date'),
                            key_responsibilities=exp.get('key_responsibilities', '')
                        )
                    else:
                        Experiences.objects.create(
                            user=instance,
                            company_name=exp.get('company_name', ''),
                            position=exp.get('position', ''),
                            experience_start_date=exp.get('experience_start_date'),
                            experience_end_date=exp.get('experience_end_date'),
                            key_responsibilities=exp.get('key_responsibilities', '')
                        )
            except Exception as e:
                print(f"Experience Error: {e}")

        deleted_exp_ids = self.initial_data.get('deleted_experience_ids', [])
        if isinstance(deleted_exp_ids, str):
            try:
                deleted_exp_ids = json.loads(deleted_exp_ids)
            except json.JSONDecodeError:
                deleted_exp_ids = []
        Experiences.objects.filter(id__in=deleted_exp_ids, user=instance).delete()

        # Handle Portfolio
        if self.portfolio_data:
            try:
                for i, proj in enumerate(json.loads(self.portfolio_data)):
                    project_id = proj.get("id")
                    image_file = self.project_images.get(str(i))
                    if project_id:
                        Portfolio.objects.filter(id=project_id, user=instance).update(
                            project_title=proj.get('project_title', ''),
                            project_description=proj.get('project_description', ''),
                            project_url=proj.get('project_url', ''),
                            project_image=image_file if image_file else ('project_image')
                        )
                    else:
                        Portfolio.objects.create(
                            user=instance,
                            project_title=proj.get('project_title', ''),
                            project_description=proj.get('project_description', ''),
                            project_url=proj.get('project_url', ''),
                            project_image=image_file
                        )
            except Exception as e:
                print(f"Portfolio Error: {e}")

        deleted_proj_ids = self.initial_data.get('deleted_project_ids', [])
        if isinstance(deleted_proj_ids, str):
            try:
                deleted_proj_ids = json.loads(deleted_proj_ids)
            except json.JSONDecodeError:
                deleted_proj_ids = []
        Portfolio.objects.filter(id__in=deleted_proj_ids, user=instance).delete()

        # Handle Certifications
        if self.certifications_data:
            try:
                for i, cert in enumerate(json.loads(self.certifications_data)):
                    image_file = self.certification_images.get(str(i))  # <- define here
                    cert_id = cert.get("id")
                    if cert_id:
                        Certification.objects.filter(id=cert_id, user=instance).update(
                            certifications_name=cert.get('certifications_name', ''),
                            certifications_issuer=cert.get('certifications_issuer', ''),
                            certifications_issued_date=cert.get('certifications_issued_date'),
                            certifications_expiration_date=cert.get('certifications_expiration_date'),
                            certifications_id=cert.get('certifications_id', ''),
                            certifications_image_url=cert.get('certifications_image_url', ''),
                            certifications_image=image_file if image_file else None
                        )
                    else:
                        Certification.objects.create(
                            user=instance,
                            certifications_name=cert.get('certifications_name', ''),
                            certifications_issuer=cert.get('certifications_issuer', ''),
                            certifications_issued_date=cert.get('certifications_issued_date'),
                            certifications_expiration_date=cert.get('certifications_expiration_date'),
                            certifications_id=cert.get('certifications_id', ''),
                            certifications_image_url=cert.get('certifications_image_url', ''),
                            certifications_image=image_file
                        )
            except Exception as e:
                print(f"Certification Error: {e}")
            deleted_cert_ids = self.initial_data.get('deleted_certification_ids', [])

        # Handle Categories
        categories_data = self.categories_data
        if isinstance(categories_data, str):
            try:
                categories_data = json.loads(categories_data)
            except json.JSONDecodeError:
                categories_data = []

        if isinstance(categories_data, list):
            for cat in categories_data:
                try:
                    cat_id = cat.get("id")
                    if cat_id:
                        ServiceCategory.objects.filter(id=cat_id, user=instance).update(
                            services_categories=cat.get('services_categories', ''),
                            services_description=cat.get('services_description', ''),
                            rate_range=cat.get('rate_range', ''),
                            availability=cat.get('availability', '')
                        )
                    else:
                        ServiceCategory.objects.create(
                            user=instance,
                            services_categories=cat.get('services_categories', ''),
                            services_description=cat.get('services_description', ''),
                            rate_range=cat.get('rate_range', ''),
                            availability=cat.get('availability', '')
                        )
                except Exception as e:
                    print(f"Category Error: {e}")

        deleted_cat_ids = self.initial_data.get('deleted_category_ids', [])
        if isinstance(deleted_cat_ids, str):
            try:
                deleted_cat_ids = json.loads(deleted_cat_ids)
            except json.JSONDecodeError:
                deleted_cat_ids = []
        ServiceCategory.objects.filter(id__in=deleted_cat_ids, user=instance).delete()


        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()

        return instance




#request password serlizers
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

#profile share serilizers
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
            'portfolio'
        ]

class UsersearchSerializer(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ('id', 'username', 'description', 'rating')

    def get_description(self, obj):
        return obj.bio or "N/A"

    def get_rating(self, obj):
        return obj.max_individual_rating or 0