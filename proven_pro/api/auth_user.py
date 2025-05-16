
import uuid
from .serializers import RegisterSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
import requests
from .serializers import RegisterSerializer, RequestPasswordResetSerializer, PasswordResetConfirmSerializer
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
import logging  # Add this import               
from django.conf import settings
from django.core.mail import send_mail
from .models import Users


User = get_user_model()



#google_auth_view
@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    print("Google auth endpoint called")
    print(f"Request data: {request.data}")
    
    token = request.data.get('token')
    if not token:
        print("No token provided")
        return Response({'error': 'Google token is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Use Google endpoint to validate ID token
        response = requests.get(
            'https://oauth2.googleapis.com/tokeninfo',
            params={'id_token': token}
        )
        
        print(f"Google response status: {response.status_code}")
        if response.content:
            print(f"Google response content: {response.content[:200]}")
        
        if not response.ok:
            # Try alternative endpoint
            response = requests.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            print(f"Second attempt - Google response status: {response.status_code}")
            if response.content:
                print(f"Second attempt - Google response content: {response.content[:200]}")
            
            if not response.ok:
                return Response({
                    'error': 'Invalid Google token',
                    'google_status': response.status_code,
                    'google_response': response.text
                }, status=status.HTTP_401_UNAUTHORIZED)

        google_data = response.json()
        print(f"Google data received: {google_data}")

        email = google_data.get('email')
        google_id = google_data.get('sub')
        name = google_data.get('name', '')

        if not email or not google_id:
            return Response({'error': 'Email or ID missing'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user exists
        try:
            user = User.objects.filter(email=email).first()
            
            if user:
                print(f"Found existing user: {user.email}")
                # If user already exists but google_id not set
                if not user.google_id:
                    print(f"Updating existing user with Google ID: {google_id}")
                    user.google_id = google_id
                    user.is_google_user = True
                    user.save()
            else:
                # Create new user
                print(f"Creating new user with email: {email}")
                name_parts = name.split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                username = f'google_{google_id[:10]}'
                
                # Make username unique if needed
                i = 1
                temp_username = username
                while User.objects.filter(username=temp_username).exists():
                    temp_username = f"{username}_{i}"
                    i += 1
                username = temp_username
                
                # Use create_user method for proper password hashing
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=str(uuid.uuid4()),  # Random password
                    google_id=google_id,
                    is_google_user=True,
                    first_name=first_name,
                    last_name=last_name,
                    subscription_type='free'
                )
                print(f"Created new user: {user.email}")

            # Generate JWT
            refresh = RefreshToken.for_user(user)
            print(f"Generated tokens for user: {user.email}")

            return Response({
                'message': 'Login successful!',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            })

        except Exception as user_error:
            print(f"Error handling user: {str(user_error)}")
            import traceback
            print(traceback.format_exc())
            return Response({'error': f'User processing error: {str(user_error)}'}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        import traceback
        print(f"Error in google_auth: {str(e)}")
        print(traceback.format_exc())
        return Response({'error': f'Unexpected error: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegisterView(APIView):
    def post(self, request):
        # Handle verification link clicks (YES/NO)
        email = request.query_params.get("email")
        choice = request.query_params.get("verify")

        if email and choice:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

            if choice == "yes":
                user.is_verified = True
                user.save()
                return Response({"message": "Registration successful!"}, status=status.HTTP_200_OK)
            elif choice == "no":
                user.delete()
                return Response({"message": "Registration cancelled."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid choice."}, status=status.HTTP_400_BAD_REQUEST)

        # Handle initial registration request
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            user = User.objects.create_user(**validated_data)
            user.is_verified = False
            user.save()

            base_url = "http://127.0.0.1:8000"  # change to your backend/frontend domain
            yes_url = f"{base_url}/api/register/?email={user.email}&verify=yes"
            no_url = f"{base_url}/api/register/?email={user.email}&verify=no"

            message = f"""
Hi {user.username},

Please confirm your registration:

✅ YES - {yes_url}
❌ NO - {no_url}
"""

            send_mail(
                "Confirm Your Registration",
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return Response({"message": "Verification email sent. Please confirm."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# Login View (Custom response with tokens)

class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = Users.objects.filter(email=email).first()

        if user:
            # Check if the is_verified field exists before checking it
            if hasattr(user, 'is_verified') and not user.is_verified:
                return Response({"detail": "Account not verified. Please confirm registration from your email."}, status=status.HTTP_403_FORBIDDEN)

            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    "message": "Login successful!",
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    }
                }, status=status.HTTP_200_OK)

        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class RequestResetPasswordView(APIView):
    def post(self, request):
        # Import necessary modules
        import re  # Add this import
        import logging
        from django.core.mail import EmailMultiAlternatives
        
        serializer = RequestPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_link = f"{settings.FRONTEND_URL}/ResetPassword?uid={uid}&token={token}"

            # HTML email content
            html_message = f"""
            <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>Hello,</p>
                    <p>You've requested to reset your password. Click the link below to reset it:</p>
                    <p><a href="{reset_link}">Reset Your Password</a></p>
                    <p>Or copy and paste this link in your browser:</p>
                    <p>{reset_link}</p>
                    <p>If you didn't request this, please ignore this email.</p>
                    <p>This link will expire soon for security reasons.</p>
                    <br>
                    <p>Best regards,<br>The Team</p>
                </body>
            </html>
            """

            # Plain text version
            text_message = f"""
            Password Reset Request

            Hello,

            You've requested to reset your password. Please visit this link to reset it:
            {reset_link}

            If you didn't request this, please ignore this email.
            This link will expire soon for security reasons.

            Best regards,
            The Team
            """

            try:
                subject = "Reset Your Password"
                email_message = EmailMultiAlternatives(
                    subject=subject,
                    body=text_message,
                    from_email=settings.EMAIL_HOST_USER,
                    to=[email],
                )
                email_message.attach_alternative(html_message, "text/html")
                email_message.send(fail_silently=False)

                return Response({
                    "message": "Password reset link sent to your email.",
                    "success": True
                })

            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Password reset email failed: {str(e)}")
                return Response({
                    "error": "Failed to send password reset email. Please try again later.",
                    "details": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token and set new password
    """
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            # Decode the user ID
            decoded_uid = force_str(urlsafe_base64_decode(uid))
            
            # If your User model uses UUID as primary key
            try:
                user_uuid = uuid.UUID(decoded_uid)
                user = User.objects.get(pk=user_uuid)
            except (ValueError, TypeError):
                # If conversion to UUID fails, try as string/int
                user = User.objects.get(pk=decoded_uid)
            
            # Check if the token is valid
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({"message": "Password reset successful."})
            else:
                return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
                
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#Logout View
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout successful."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


