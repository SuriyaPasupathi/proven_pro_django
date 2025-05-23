from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework import viewsets, permissions, status
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from .serializers import UserProfileSerializer, ReviewSerializer, PublicProfileSerializer
from .models import Users, Review, ProfileShare, Experience, Certification, ServiceCategory, Portfolio
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
        data = request.data.copy()
        
        # Print received data for debugging
        print("Received data:", data)
        
        # Handle portfolio/projects data
        if 'portfolio' in data:
            try:
                # Parse portfolio data
                portfolio_data = data.pop('portfolio')
                if isinstance(portfolio_data, str):
                    try:
                        # Try to parse as JSON
                        portfolio_items = json.loads(portfolio_data)
                    except json.JSONDecodeError:
                        # If it's not valid JSON, treat it as a list with one item
                        portfolio_items = [portfolio_data]
                else:
                    portfolio_items = portfolio_data
                
                print("Portfolio items:", portfolio_items)
                
                # Clear existing portfolios
                user.portfolios.all().delete()
                
                # Create new portfolios
                if isinstance(portfolio_items, list):
                    for item in portfolio_items:
                        # If item is a string that looks like JSON, parse it
                        if isinstance(item, str) and item.startswith('[') and item.endswith(']'):
                            try:
                                items = json.loads(item)
                                for sub_item in items:
                                    if isinstance(sub_item, dict):
                                        portfolio_data = {
                                            'project_title': sub_item.get('project_title', ''),
                                            'project_description': sub_item.get('project_description', ''),
                                            'project_url': sub_item.get('project_url', '')
                                        }
                                        
                                        # Create the portfolio
                                        portfolio = Portfolio.objects.create(user=user, **portfolio_data)
                                        
                                        # Handle project image if it exists
                                        if 'project_image' in request.FILES:
                                            portfolio.project_image = request.FILES['project_image']
                                            portfolio.save()
                                            
                                        print(f"Created portfolio: {portfolio.project_title}")
                            except json.JSONDecodeError:
                                print(f"Error parsing portfolio item: {item}")
                        elif isinstance(item, dict):
                            portfolio_data = {
                                'project_title': item.get('project_title', ''),
                                'project_description': item.get('project_description', ''),
                                'project_url': item.get('project_url', '')
                            }
                            
                            # Create the portfolio
                            portfolio = Portfolio.objects.create(user=user, **portfolio_data)
                            
                            # Handle project image if it exists
                            if 'project_image' in request.FILES:
                                portfolio.project_image = request.FILES['project_image']
                                portfolio.save()
                                
                            print(f"Created portfolio: {portfolio.project_title}")
            except Exception as e:
                print(f"Error processing portfolio data: {e}")
                import traceback
                traceback.print_exc()
        
        # Handle individual project data if not using portfolio
        elif 'project_title' in data:
            try:
                # Clear existing portfolios
                user.portfolios.all().delete()
                
                # Get project data
                portfolio_data = {
                    'project_title': data.pop('project_title', ''),
                    'project_description': data.pop('project_description', ''),
                    'project_url': data.pop('project_url', '')
                }
                
                # Create the portfolio
                portfolio = Portfolio.objects.create(user=user, **portfolio_data)
                
                # Handle project image if it exists
                if 'project_image' in request.FILES:
                    portfolio.project_image = request.FILES['project_image']
                    portfolio.save()
                    
                print(f"Created portfolio: {portfolio.project_title}")
            except Exception as e:
                print(f"Error creating portfolio: {e}")
                import traceback
                traceback.print_exc()
        
        # Handle services_categories separately
        if 'services_categories' in data:
            services_categories = data.pop('services_categories')
            print("Services categories (raw):", services_categories)
            
            # Try to parse if it's a string
            if isinstance(services_categories, str):
                try:
                    if services_categories.startswith('[') and services_categories.endswith(']'):
                        services_categories = json.loads(services_categories)
                    else:
                        services_categories = [services_categories]
                except Exception as e:
                    print(f"Error parsing services_categories: {e}")
                    services_categories = [services_categories]
            
            # Ensure it's a list
            if not isinstance(services_categories, list):
                services_categories = [services_categories]
            
            print("Services categories (processed):", services_categories)
            
            # Get related fields
            services_description = data.get('services_description', '')
            rate_range = data.get('rate_range', '')
            availability = data.get('availability', '')
            
            # Clear existing service categories
            user.service_categories.all().delete()
            
            # Create new service categories
            for category in services_categories:
                ServiceCategory.objects.create(
                    user=user,
                    services_categories=category,
                    services_description=services_description,
                    rate_range=rate_range,
                    availability=availability
                )
        
        # Handle experience data
        if 'company_name' in data:
            try:
                # Clear existing experiences
                user.experiences.all().delete()
                
                # Get experience data
                experience_data = {
                    'company_name': data.pop('company_name', ''),
                    'position': data.pop('position', ''),
                    'key_responsibilities': data.pop('key_responsibilities', ''),
                    'experience_start_date': data.pop('experience_start_date', None),
                    'experience_end_date': data.pop('experience_end_date', None)
                }
                
                # Create new experience
                Experience.objects.create(user=user, **experience_data)
                print("Created experience successfully")
            except Exception as e:
                print(f"Error creating experience: {e}")
        
        # Handle certification data
        if 'certification' in data:
            try:
                # Parse certification data
                certification_data = data.pop('certification')
                if isinstance(certification_data, str):
                    try:
                        # Try to parse as JSON
                        certification_items = json.loads(certification_data)
                    except json.JSONDecodeError:
                        # If it's not valid JSON, treat it as a single item
                        certification_items = [{'certifications_name': certification_data}]
                else:
                    certification_items = certification_data
                
                print("Certification items:", certification_items)
                
                # Clear existing certifications
                user.certifications.all().delete()
                
                # Create new certifications
                if isinstance(certification_items, list):
                    for item in certification_items:
                        # If item is a string that looks like JSON, parse it
                        if isinstance(item, str) and item.startswith('[') and item.endswith(']'):
                            try:
                                items = json.loads(item)
                                for sub_item in items:
                                    if isinstance(sub_item, dict):
                                        cert_data = {
                                            'certifications_name': sub_item.get('certifications_name', ''),
                                            'certifications_issuer': sub_item.get('certifications_issuer', ''),
                                            'certifications_issued_date': sub_item.get('certifications_issued_date', timezone.now().date()),
                                            'certifications_expiration_date': sub_item.get('certifications_expiration_date'),
                                            'certifications_id': sub_item.get('certifications_id', '')
                                        }
                                        
                                        # Create the certification
                                        cert = Certification.objects.create(user=user, **cert_data)
                                        
                                        # Handle certification image if it exists
                                        if 'certifications_image' in request.FILES:
                                            cert.certifications_image = request.FILES['certifications_image']
                                            cert.save()
                                            
                                        print(f"Created certification: {cert.certifications_name}")
                            except json.JSONDecodeError:
                                print(f"Error parsing certification item: {item}")
                        elif isinstance(item, dict):
                            cert_data = {
                                'certifications_name': item.get('certifications_name', ''),
                                'certifications_issuer': item.get('certifications_issuer', ''),
                                'certifications_issued_date': item.get('certifications_issued_date', timezone.now().date()),
                                'certifications_expiration_date': item.get('certifications_expiration_date'),
                                'certifications_id': item.get('certifications_id', '')
                            }
                            
                            # Create the certification
                            cert = Certification.objects.create(user=user, **cert_data)
                            
                            # Handle certification image if it exists
                            if 'certifications_image' in request.FILES:
                                cert.certifications_image = request.FILES['certifications_image']
                                cert.save()
                                
                            print(f"Created certification: {cert.certifications_name}")
            except Exception as e:
                print(f"Error processing certification data: {e}")
                import traceback
                traceback.print_exc()
        
        # Create a serializer with the remaining data
        serializer = UserProfileSerializer(
            user,
            data=data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            instance = serializer.save()
            
            # Return updated user data
            updated_serializer = UserProfileSerializer(instance, context={'request': request})
            return Response({
                'message': 'Profile updated successfully',
                'data': updated_serializer.data
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



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_profile_share(request, token):
    try:
        # Convert string token to UUID if needed
        if isinstance(token, str):
            token = uuid.UUID(token)
            
        share = ProfileShare.objects.select_related('user').get(share_token=token)
        
        # Check if share is expired
        if timezone.now() > share.expires_at:
            return Response(
                {'error': 'This link has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Serialize the profile data
        serializer = PublicProfileSerializer(share.user)
        return Response({
            'profile': serializer.data,
            'share_token': str(share.share_token)
        })
        
    except (ProfileShare.DoesNotExist, ValueError, TypeError):
        return Response(
            {'error': 'Invalid share token'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_profile_share(request):
    user = request.user
    recipient_email = request.data.get('email')
    
    if not recipient_email:
        return Response({'error': 'Recipient email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate share token
    share_token = user.generate_share_link(recipient_email)
    
    # Send email with share link
    verification_url = f"{settings.FRONTEND_URL}/verify-profile/{share_token}"
    
    try:
        # Context for the template
        context = {
            'user_name': user.name,
            'verification_url': verification_url
        }
        
        # Render HTML content from template
        html_content = render_to_string('emails/profile_share.html', context)
        
        # Create a simple text version from the HTML for email clients that don't support HTML
        # This is automatically handled by EmailMessage
        
        subject = f"Profile Review Request from {user.name}"
        from_email = settings.EMAIL_HOST_USER
        
        # Send email with HTML content
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=from_email,
            to=[recipient_email],
        )
        email.content_subtype = "html"  # Set the primary content to be HTML
        email.send(fail_silently=False)
        
        return Response({
            'message': 'Share link sent successfully',
            'share_token': share_token,
            'verification_url': verification_url
        })
        
    except Exception as e:
        # Log the error for debugging
        logger = logging.getLogger(__name__)
        logger.error(f"Email sending failed: {str(e)}")
        
        # Still return success since the share link was created
        return Response({
            'message': 'Share link created but email sending failed. Please share the link manually.',
            'share_token': share_token,
            'verification_url': verification_url
        }, status=status.HTTP_201_CREATED)        
    except UserProfileSerializer.DoesNotExist:
        return Response(
            {'error': 'Profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
def submit_review(request, token):
    try:
        # Get the share object and validate it
        share = ProfileShare.objects.get(share_token=token)
        if not share.is_valid():
            return Response({'error': 'Link expired or invalid'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create review data using the user from the share object
        review_data = {
            'user': share.user.id,  # Changed from 'profile' to 'user'
            'reviewer_name': request.data.get('reviewer_name'),
            'rating': request.data.get('rating'),
            'comment': request.data.get('comment')
        }
        
        # Validate that required fields are present
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
        return Response({
            'error': 'Invalid share token'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error submitting review: {str(e)}")
        return Response({
            'error': 'An error occurred while submitting the review'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reviews(request):
    # Get the current user
    user = request.user
    
    # Get all reviews for this user
    reviews = Review.objects.filter(user=user).order_by('-created_at')
    
    # Serialize and return the reviews
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)

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
