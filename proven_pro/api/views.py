from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework import viewsets, permissions, status
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from .serializers import UserProfileSerializer, ReviewSerializer, PublicProfileSerializer
import json , os
from .models import Review, ProfileShare
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

Users = get_user_model()

def health_check(request):
    return JsonResponse({"status_api_working": "ok"})

# Correct full path to JSON file inside your app folder
json_file_path = os.path.join(settings.BASE_DIR, 'api', 'profile_fields.json')
print(json_file_path,"asdgiuagsiudysa")
with open(json_file_path) as file:
    profile_fields = json.load(file)
    SUBSCRIPTION_FIELDS = profile_fields["SUBSCRIPTION_FIELDS"]
    FILE_FIELDS = profile_fields["FILE_FIELDS"]
    URL_FIELDS = profile_fields["URL_FIELDS"] 

class UserProfileView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Serialize the user with all related data
        serializer = UserProfileSerializer(user)
        
        # Return the complete serialized data without filtering
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        # Handle file uploads and data separately to avoid pickling errors
        data = {}
        files = {}
        
        # Safely extract data fields
        for key in request.data:
            if key in request.FILES:
                files[key] = request.FILES[key]
            else:
                data[key] = request.data[key]
        
        # Print the data for debugging
        print("Received data:", data)
        print("Received files:", files)
        
        # Handle project_image_url and project_image specially
        if 'project_image_url' in data:
            # Remove project_image_url from data as it's not needed for saving
            data.pop('project_image_url')
        
        # If project_image is a string but not a file, remove it
        if 'project_image' in data and not isinstance(data['project_image'], (list, tuple)) and not data['project_image'].startswith('data:'):
            try:
                # Check if it's a JSON string
                import json
                json_data = json.loads(data['project_image'])
                # If it's an empty object or list, remove it
                if not json_data or (isinstance(json_data, list) and len(json_data) == 0):
                    data.pop('project_image')
            except:
                # If it's not valid JSON, keep it (might be a file path)
                pass
        
        # Remove project_image if it's a string representation of an empty array or object
        if 'project_image' in data and isinstance(data['project_image'], str):
            if data['project_image'] in ['[]', '{}', '[{}]']:
                data.pop('project_image')
        
        # Create a serializer with both data and files
        serializer = UserProfileSerializer(user, data=data, partial=True)
        
        if serializer.is_valid():
            # Save the data fields
            instance = serializer.save()
            
            # Handle file fields separately
            for key, file in files.items():
                setattr(instance, key, file)
            
            # Save again if there were files
            if files:
                instance.save()
            
            return Response({
                'message': 'Profile updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            print("Serializer errors:", serializer.errors)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        user = request.user
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class UserSearchFilterView(APIView):
    permission_classes = [AllowAny]  # Change to IsAuthenticated if needed

    def get(self, request):
        query = request.GET.get('q', '')
        job_title = request.GET.get('job_title')
        specialization = request.GET.get('job_specialization')
        language = request.GET.get('language')
        sort_by = request.GET.get('sort_by')  # e.g., 'rating' or 'first_name'

        users = Users.objects.all()

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

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def profile_share_actions(request):
    action = request.query_params.get('action') if request.method == 'GET' else request.data.get('action')

    # ✅ 1. Verify Profile via Share Token
    if request.method == 'GET' and action == 'verify':
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

    # ✅ 2. Generate Profile Share Link and Send Email
    if request.method == 'POST' and action == 'generate':
        user = request.user
        recipient_email = request.data.get('email')

        if not recipient_email:
            return Response({'error': 'Recipient email is required'}, status=status.HTTP_400_BAD_REQUEST)

        share_token = user.generate_share_link(recipient_email)
        verification_url = f"{settings.FRONTEND_URL}/profile/{share_token}"

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

    # ✅ 3. Submit a Review
    if request.method == 'POST' and action == 'submit':
        token = request.data.get('token')
        try:
            share = ProfileShare.objects.get(share_token=token)
            if not share.is_valid():
                return Response({'error': 'Link expired or invalid'}, status=status.HTTP_400_BAD_REQUEST)

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

    # ✅ 4. Get All Reviews for Current User
    if request.method == 'GET' and action == 'get_reviews':
        user = request.user
        reviews = Review.objects.filter(user=user).order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    return Response({'error': 'Invalid action or method'}, status=status.HTTP_400_BAD_REQUEST)

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
        user = request.user
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
        
        # Return updated verification status
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
        user = request.user
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
        user = request.user
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_document_approval_webhook(request):
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
