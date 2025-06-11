from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework import viewsets, permissions, status
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from .serializers import UserProfileSerializer, ReviewSerializer, PublicProfileSerializer,JobPositionserializers,Skills_serializers,Tools_Skills_serializers,Service_drop_down_serializers, UsersearchSerializer
import json , os
from .models import Review, ProfileShare,Service_drop_down,JobPosition,ToolsSkillsCategory,Skill
from django.conf import settings
from django.utils import timezone
import uuid
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.mail import send_mail
import requests
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMultiAlternatives
import logging
# from twilio.rest import Client
import random
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
import logging
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.db.models import Max, Count, Q, Avg
from django.core.paginator import Paginator

Users = get_user_model()

def health_check(request):
    return JsonResponse({"status_api_working": "ok"})

# Correct full path to JSON file inside your app folder
json_file_path = os.path.join(settings.BASE_DIR, 'api', 'profile_fields.json')

with open(json_file_path) as file:
    profile_fields = json.load(file)
    SUBSCRIPTION_FIELDS = profile_fields["SUBSCRIPTION_FIELDS"]
    FILE_FIELDS = profile_fields["FILE_FIELDS"]
    URL_FIELDS = profile_fields["URL_FIELDS"] 

class UserProfileView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = Users.objects.get(id=user_id)
            serializer = UserProfileSerializer(user)
            return Response(serializer.data)
        except Users.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        user = request.user
        data = {}
        files = {}

        for key in request.data:
            if key in request.FILES:
                files[key] = request.FILES[key]
            else:
                data[key] = request.data[key]

        print("Received data:", data)
        print("Received files keys:", files.keys())

        serializer_data = data.copy()
        for key, value in files.items():
            serializer_data[key] = value

        serializer = UserProfileSerializer(user, data=serializer_data, partial=True)

        if serializer.is_valid():
            print("Serializer validated_data:", serializer.validated_data)
            serializer.save()
            return Response({
                "message": "Profile updated successfully",
                "data": UserProfileSerializer(user).data
            })
        else:
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        user_id = request.query_params.get('user_id')  # get from query param
        if not user_id:
            return Response({"error": "user_id query parameter is required"}, status=400)

        try:
            user = Users.objects.get(id=user_id)  # use your custom user model here
        except Users.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({"error": "user_id query parameter is required"}, status=400)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        user.delete()
        return Response({"message": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class DropdownAPIView(APIView):
    def get(self, request):
        dropdown_type = request.query_params.get('type')

        if dropdown_type == 'services':
            data = Service_drop_down.objects.all()
            serializer = Service_drop_down_serializers(data, many=True)
            return Response(serializer.data)

        elif dropdown_type == 'jobpositions':
            data = JobPosition.objects.all()
            serializer = JobPositionserializers(data, many=True)
            return Response(serializer.data)

        return Response({'detail': 'Invalid type'}, status=status.HTTP_400_BAD_REQUEST)

class SkillsDropdownAPIView(APIView):
    def get(self, request):
        category_filter = request.query_params.get('category')

        if category_filter:
            try:
                category = ToolsSkillsCategory.objects.get(name__iexact=category_filter)
                serializer = Tools_Skills_serializers(category)
                return Response(serializer.data)
            except ToolsSkillsCategory.DoesNotExist:
                # Show available categories in the error response
                categories = list(ToolsSkillsCategory.objects.values_list('name', flat=True))
                return Response({
                    'detail': 'Category not found',
                    'available_categories': categories
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            data = ToolsSkillsCategory.objects.prefetch_related('skills').all()
            serializer = Tools_Skills_serializers(data, many=True)
            return Response(serializer.data)

class UserSearchFilterView(APIView):
    permission_classes = [AllowAny]  # Change to IsAuthenticated if needed

    def get(self, request):
        query = request.GET.get('q', '')
        job_title = request.GET.get('job_title')
        specialization = request.GET.get('job_specialization')
        language = request.GET.get('language')
        sort_by = request.GET.get('sort_by')  # e.g., 'rating' or 'first_name'

        users = UserProfileSerializer.objects.all()

        # Filtering
        if query:
            users = users.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(bio__icontains=query) |
                Q(skills__icontains=query) |
                Q(services__icontains=query)
            )

        if job_title:
            users = users.filter(job_title__icontains=job_title)

        if specialization:
            users = users.filter(job_specialization__icontains=specialization)

        if language:
            users = users.filter(languages__icontains=language)

        # Sorting
        if sort_by == 'rating':
            users = users.order_by('-rating')  # highest rating first
        elif sort_by == 'first_name':
            users = users.order_by('first_name')

        serializer = UserProfileSerializer(users, many=True)
        return Response(serializer.data)

logger = logging.getLogger(__name__)
class profile_share_actions(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        action = request.query_params.get('action')
        user_id = request.query_params.get('user_id')

        # 1. Verify Profile via Share Token
        if action == 'verify':
            token = request.query_params.get('token')
            try:
                token = uuid.UUID(token)
                share = ProfileShare.objects.select_related('user').get(share_token=token)

                if timezone.now() > share.expires_at:
                    return Response({'error': 'This link has expired'}, status=status.HTTP_400_BAD_REQUEST)

                serializer = PublicProfileSerializer(share.user)
                return Response({
                    'profile': serializer.data,
                    'share_token': str(share.share_token)
                })

            except (ProfileShare.DoesNotExist, ValueError, TypeError):
                return Response({'error': 'Invalid share token'}, status=status.HTTP_404_NOT_FOUND)

        # 3. Get All Reviews for Specific User (user_id-based)
        elif action == 'get_reviews':
            if not user_id:
                return Response({'error': 'user_id query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                user = Users.objects.get(id=user_id)
            except Users.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            reviews = Review.objects.filter(user=user).order_by('-created_at')
            serializer = ReviewSerializer(reviews, many=True)
            return Response(serializer.data)

        return Response({'error': 'Invalid action or method'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        action = request.data.get('action')
        user_id = request.data.get('user_id')

        # 2. Generate Profile Share Link and Send Email (user_id-based)
        if action == 'generate':
            if not user_id:
                return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = Users.objects.get(id=user_id)
            except Users.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            recipient_email = request.data.get('email')
            if not recipient_email:
                return Response({'error': 'Recipient email is required'}, status=status.HTTP_400_BAD_REQUEST)

            share_token = user.generate_share_link(recipient_email)
            verification_url = f"{settings.FRONTEND_URL}/share/{user.id}/{share_token}"

            try:
                context = {
                    'user_name': user.name,
                    'verification_url': verification_url
                }
                html_content = render_to_string('emails/profile_share.html', context)

                subject = f"Profile Review Request from {user.name}"
                email = EmailMessage(
                    subject=subject,
                    body=html_content,
                    from_email=settings.EMAIL_HOST_USER,
                    to=[recipient_email],
                )
                email.content_subtype = "html"
                email.send(fail_silently=False)

                return Response({
                    'message': 'Share link sent successfully',
                    'share_token': share_token,
                    'verification_url': verification_url
                })

            except Exception as e:
                logger.error(f"Email sending failed: {str(e)}")
                return Response({
                    'message': 'Share link created but email sending failed. Please share the link manually.',
                    'share_token': share_token,
                    'verification_url': verification_url
                }, status=status.HTTP_201_CREATED)

        return Response({'error': 'Invalid action or method'}, status=status.HTTP_400_BAD_REQUEST)

class submit_profile_review(APIView):
    permission_classes = [AllowAny]  # Public access via token

    def post(self, request):
        token = request.data.get('share_token')
        try:
            share = ProfileShare.objects.get(share_token=token)

            if not share.is_valid():
                return Response({'error': 'Link expired or invalid'}, status=status.HTTP_400_BAD_REQUEST)

            # Get user from the share object (user_id is internal)
            review_data = {
                'user': share.user.id,
                'reviewer_name': request.data.get('reviewer_name'),
                'rating': request.data.get('rating'),
                'comment': request.data.get('comment')
            }

            if not all([review_data['reviewer_name'], review_data['rating'], review_data['comment']]):
                return Response({
                    'error': 'reviewer_name, rating, and comment are required fields'
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = ReviewSerializer(data=review_data)
            if serializer.is_valid():
                review = serializer.save()
                return Response({
                    'message': 'Review submitted successfully',
                    'review': ReviewSerializer(review).data
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except ProfileShare.DoesNotExist:
            return Response({'error': 'Invalid share token'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error submitting review: {str(e)}")
            return Response({'error': 'An error occurred while submitting the review'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CheckProfileStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Check if the user has completed their profile
        """
        user = request.user
        
        # Check if essential profile fields are filled
        has_profile = bool(
            user.first_name and 
            user.last_name 
        )
        
        # Add more detailed profile completion information
        profile_fields = {
            'first_name': bool(user.first_name),
            'last_name': bool(user.last_name),
            'bio': bool(getattr(user, 'bio', None)),
            'profile_picture': bool(getattr(user, 'profile_picture', None)),
            'skills': bool(getattr(user, 'skills', None))
        }
        
        # Calculate completion percentage
        completed_fields = sum(1 for value in profile_fields.values() if value)
        total_fields = len(profile_fields)
        completion_percentage = int((completed_fields / total_fields) * 100)
        
        return Response({
            'has_profile': has_profile,
            'subscription_type': user.subscription_type,
            'profile_completion': {
                'percentage': completion_percentage,
                'fields': profile_fields
            },
            'next_steps': self._get_next_steps(profile_fields)
        })
    
    def _get_next_steps(self, profile_fields):
        """
        Generate suggestions for next steps to complete profile
        """
        next_steps = []
        
        if not profile_fields['first_name'] or not profile_fields['last_name']:
            next_steps.append("Add your full name")
        
        if not profile_fields['bio']:
            next_steps.append("Write a professional bio")
        
        if not profile_fields['profile_picture']:
            next_steps.append("Upload a profile picture")
        
        if not profile_fields['skills']:
            next_steps.append("Add your skills")
        
        return next_steps
class UploadVerificationDocumentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user_id = request.query_params.get('user_id')  # Get user ID from query params
        if not user_id:
            return Response({'error': 'user_id query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(id=user_id)  # Replace with your actual user model
        except Users.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        doc_type = request.data.get('document_type')
        if not doc_type or doc_type not in ['gov_id', 'address']:
            return Response({'error': 'Invalid document type'}, status=status.HTTP_400_BAD_REQUEST)

        if 'document' not in request.FILES:
            return Response({'error': 'No document provided'}, status=status.HTTP_400_BAD_REQUEST)

        document = request.FILES['document']

        if doc_type == 'gov_id':
            user.gov_id_document = document
        elif doc_type == 'address':
            user.address_document = document

        user.save()

        return Response({
            'message': f'{doc_type.replace("_", " ").title()} document uploaded successfully',
            'verification_status': user.verification_status
        })

class RequestMobileVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        mobile = request.data.get('mobile')
        
        if not mobile:
            return Response({'error': 'Mobile number is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Update user's mobile number
        user.mobile = mobile
        user.save()
        
        # Generate OTP
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Store OTP in session
        request.session['mobile_otp'] = otp
        request.session['mobile_to_verify'] = mobile
        
        try:
            # Send OTP via Twilio
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=f"Your Proven Pro verification code is: {otp}",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=mobile
            )
            
            return Response({
                'message': 'Verification code sent to your mobile number',
                'sid': message.sid
            })
        except Exception as e:
            logging.error(f"Twilio error: {str(e)}")
            return Response({
                'error': 'Failed to send verification code',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyMobileOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.query_params.get('user_id')  # Get user ID from query params
        if not user_id:
            return Response({'error': 'user_id query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(id=user_id)  # Replace with your actual user model
        except Users.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        otp = request.data.get('otp')

        stored_otp = request.session.get('mobile_otp')
        mobile_to_verify = request.session.get('mobile_to_verify')

        if not stored_otp or not mobile_to_verify:
            return Response({'error': 'No verification in progress'}, status=status.HTTP_400_BAD_REQUEST)

        if otp != stored_otp:
            return Response({'error': 'Invalid verification code'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify the mobile number
        user.mobile_verified = True
        user.save()

        # Clear session data
        del request.session['mobile_otp']
        del request.session['mobile_to_verify']

        return Response({
            'message': 'Mobile number verified successfully',
            'verification_status': user.verification_status
        })

class GetVerificationStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(id=user_id)
        except Users.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'verification_status': user.verification_status,
            'gov_id_verified': user.gov_id_verified,
            'address_verified': user.address_verified,
            'mobile_verified': user.mobile_verified,
            'has_gov_id_document': bool(user.gov_id_document),
            'has_address_document': bool(user.address_document),
            'mobile': user.mobile,
            'verification_details': {
                'government_id': {
                    'uploaded': bool(user.gov_id_document),
                    'verified': user.gov_id_verified,
                    'percentage': 50 if user.gov_id_verified else 0
                },
                'address_proof': {
                    'uploaded': bool(user.address_document),
                    'verified': user.address_verified,
                    'percentage': 25 if user.address_verified else 0
                },
                'mobile': {
                    'provided': bool(user.mobile),
                    'verified': user.mobile_verified,
                    'percentage': 25 if user.mobile_verified else 0
                }
            }
        })

class admin_document_approval_webhook(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Webhook for admin document approval notifications.
        This can be called from admin actions or other admin interfaces.
        """
        user_id = request.data.get('user_id')
        document_type = request.data.get('document_type')
        is_approved = request.data.get('is_approved', False)

        if not user_id or not document_type:
            return Response({
                'error': 'Missing required parameters'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(id=user_id)

            if document_type == 'gov_id':
                user.gov_id_verified = is_approved
            elif document_type == 'address':
                user.address_verified = is_approved
            else:
                return Response({
                    'error': 'Invalid document type'
                }, status=status.HTTP_400_BAD_REQUEST)

            user.save(update_fields=[f'{document_type}_verified'])

            # Send notification email
            user.send_verification_status_email(document_type, is_approved)

            return Response({
                'success': True,
                'message': f'{document_type.replace("_", " ").title()} {"approved" if is_approved else "rejected"} successfully',
                'user_id': str(user.id),
                'verification_status': user.verification_status
            })

        except Users.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)


logger = logging.getLogger(__name__)

class UsersearchApiview(APIView):
    def get(self, request):
        try:
            offset = int(request.GET.get('offset', 0))
            limit = int(request.GET.get('limit', 12))
            search = request.GET.get('search', '').strip()
            min_rating = int(request.GET.get('min_rating', 1))

            queryset = Users.objects.prefetch_related('client_reviews').annotate(
                max_individual_rating=Max('client_reviews__rating'),
                total_reviews=Count('client_reviews'),
                avg_rating=Avg('client_reviews__rating')
            )

            # ✅ Apply min_rating only if there is a rating
            queryset = queryset.filter(
                Q(max_individual_rating__isnull=True) | Q(max_individual_rating__gte=min_rating)
            )

            if search:
                queryset = queryset.filter(
                    Q(username__icontains=search) |
                    Q(bio__icontains=search) |
                    Q(primary_tools__icontains=search) |
                    Q(technical_skills__icontains=search)
                )

            queryset = queryset.order_by('-max_individual_rating', '-avg_rating', '-total_reviews')

            total_count = queryset.count()
            if total_count == 0:
                return Response({'success': True, 'data': []})

            if offset >= total_count:
                offset = offset % total_count

            users = queryset[offset:offset + limit]
            serializer = UsersearchSerializer(users, many=True)

            return Response({
                'success': True,
                'data': serializer.data
            })

        except ValueError as e:
            logger.error(f"ValueError in UsersearchApiview: {e}")
            return Response({
                'success': False,
                'error': 'Invalid parameter values',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error in UsersearchApiview: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny
# from django.template.loader import render_to_string
# from django.core.mail import EmailMultiAlternatives
# from django.conf import settings
# from rest_framework_simplejwt.tokens import RefreshToken

# import random
# import traceback
# from .models import Users
# from .serializers import RegisterSerializer

# class RegisterViewSet(viewsets.ViewSet):
#     """
#     ViewSet for handling OTP operations: registration, verification, and resending
#     """
#     permission_classes = [AllowAny]
    
#     def create(self, request):
#         """
#         Register a new user and send OTP (POST /api/otp/)
#         """
#         print(f"Registration request data: {request.data}")
        
#         try:
#             username = request.data.get('username')
#             email = request.data.get('email')
            
#             # Check if user with email already exists
#             existing_user = Users.objects.filter(email=email).first()

#             if existing_user:
#                 if existing_user.is_verified:
#                     return Response({
#                         "error": "Account already exists",
#                         "details": {
#                             "email": ["A user with this email already exists."]
#                         }
#                     }, status=status.HTTP_400_BAD_REQUEST)
#                 else:
#                     # Resend OTP if user exists but not verified
#                     self._generate_and_send_otp(existing_user)
#                     return Response({
#                         "message": "User already registered but not verified. OTP re-sent to email.",
#                         "email": existing_user.email
#                     }, status=status.HTTP_200_OK)

#             # Optional: Also check if username already exists
#             if Users.objects.filter(username=username).exists():
#                 return Response({
#                     "error": "Username already taken",
#                     "details": {
#                         "username": ["A user with that username already exists."]
#                     }
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             # Proceed with serializer validation
#             serializer = RegisterSerializer(data=request.data)
#             if not serializer.is_valid():
#                 print(f"Serializer validation failed: {serializer.errors}")
#                 return Response({
#                     "error": "Validation failed",
#                     "details": serializer.errors
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             validated_data = serializer.validated_data
#             user = Users.objects.create_user(**validated_data)
#             user.is_verified = False
#             user.save()
            
#             self._generate_and_send_otp(user)
            
#             return Response({
#                 "message": "OTP sent to your email. Please enter it to complete registration.",
#                 "email": user.email
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             print(f"Exception during registration: {str(e)}")
#             print(traceback.format_exc())
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
#     @action(detail=False, methods=['post'])
#     def verify(self, request):
#         """
#         Verify OTP for user registration (POST /api/otp/verify/)
#         """
#         otp = request.data.get("otp")
#         email = request.data.get("email")
        
#         if not otp or not email:
#             return Response({"error": "OTP and email are required"}, status=status.HTTP_400_BAD_REQUEST)
        
#         try:
#             user = Users.objects.get(email=email)

#             if user.is_verified:
#                 refresh = RefreshToken.for_user(user)
#                 return Response({
#                     "message": "User is already verified",
#                     "access": str(refresh.access_token),
#                     "refresh": str(refresh),
#                     "user": {
#                         "id": user.id,
#                         "username": user.username,
#                         "email": user.email
#                     }
#                 }, status=status.HTTP_200_OK)
            
#             if not isinstance(otp, str):
#                 otp = str(otp)
            
#             print(f"Verifying OTP: {otp} for user: {email}, stored OTP: {user.otp}")
            
#             if user.otp == otp:
#                 user.is_verified = True
#                 user.otp = None
#                 user.save()
                
#                 refresh = RefreshToken.for_user(user)
                
#                 return Response({
#                     "message": "OTP verified. Registration successful!",
#                     "access": str(refresh.access_token),
#                     "refresh": str(refresh),
#                     "user": {
#                         "id": user.id,
#                         "username": user.username,
#                         "email": user.email
#                     }
#                 }, status=status.HTTP_200_OK)
#             else:
#                 return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

#         except Users.DoesNotExist:
#             return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             print(f"Error verifying OTP: {str(e)}")
#             print(traceback.format_exc())
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
#     @action(detail=False, methods=['post'])
#     def resend(self, request):
#         """
#         Resend OTP to user's email (POST /api/otp/resend/)
#         """
#         email = request.data.get('email')
        
#         if not email:
#             return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
#         try:
#             user = Users.objects.get(email=email)
            
#             if user.is_verified:
#                 return Response({
#                     "error": "User is already verified",
#                     "verified": True
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             success = self._generate_and_send_otp(user)
            
#             if success:
#                 return Response({
#                     "message": "New OTP sent to your email",
#                     "email": user.email
#                 }, status=status.HTTP_200_OK)
#             else:
#                 return Response({
#                     "error": "Failed to send OTP email. Please try again later."
#                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
#         except Users.DoesNotExist:
#             return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             print(f"Error resending OTP: {str(e)}")
#             print(traceback.format_exc())
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
#     def _generate_and_send_otp(self, user):
#         """Generate OTP and send it to the user's email"""
#         otp_code = str(random.randint(100000, 999999))
#         user.otp = otp_code
#         user.save()
        
#         print(f"Generated OTP for user {user.email}: {otp_code}")
        
#         try:
#             context = {
#                 'username': user.username,
#                 'email': user.email,
#                 'otp_code': otp_code
#             }
            
#             html_content = render_to_string('emails/otp_email.html', context)
            
#             subject = "Your OTP for Registration"
#             from_email = settings.DEFAULT_FROM_EMAIL
#             to_email = user.email
            
#             email = EmailMultiAlternatives(
#                 subject=subject,
#                 body=html_content,
#                 from_email=from_email,
#                 to=[to_email]
#             )
#             email.attach_alternative(html_content, "text/html")
#             email.send()
            
#             print(f"OTP email sent to {to_email}")
#             return True
            
#         except Exception as email_error:
#             print(f"Failed to send OTP email: {str(email_error)}")
#             print(traceback.format_exc())
#             return False


