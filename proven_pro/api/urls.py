from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .auth_user import (
    RegisterViewSet, LoginView, google_auth, RequestResetPasswordView, 
    PasswordResetConfirmView, LogoutView,AccountSettingsView
)
from .subscription import(
   CreateSubscriptionPayment, RetrySubscriptionPayment, PayMayaWebhook)

from .views import ( 
    UserProfileView,    
    UploadVerificationDocumentView,
    RequestMobileVerificationView,
    VerifyMobileOTPView,
    GetVerificationStatusView,
    admin_document_approval_webhook,
    UserSearchFilterView,
    health_check,
    CheckProfileStatusView,
    profile_share_actions,
    submit_profile_review,
    DropdownAPIView,
    SkillsDropdownAPIView,
    UsersearchApiview,
    DeleteItemView,
    serve_media,
    BlobMediaView,
    DeleteVideoIntroView
)

router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='otp')
# router.register(r'reviews', ReviewViewSet)

urlpatterns = [
    path('health_check', health_check, name='health_check'),
  
    path('otp/verify/', RegisterViewSet.as_view({'post': 'verify'}), name='otp-verify'),
    path('otp/resend/', RegisterViewSet.as_view({'post': 'resend'}), name='otp-resend'),
     
    path('users-search/', UsersearchApiview.as_view(), name='highest-rated-users-api'),
    path('dropdown/', DropdownAPIView.as_view(), name='dropdown'),
    path('skills-dropdown/', SkillsDropdownAPIView.as_view(), name='skills-dropdown'),
    path('delete/<str:model_name>/<uuid:pk>/', DeleteItemView.as_view()),
    path('delete-video-intro/<uuid:user_id>/', DeleteVideoIntroView.as_view(), name='delete-video-intro'),

    #auth
    path('google-auth/', google_auth.as_view(), name='google-auth'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile_status/', CheckProfileStatusView.as_view(), name='profile-status'),
    path('request-reset-password/', RequestResetPasswordView.as_view(), name='request-reset-password'),
    path('reset-password-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Include router URLs
    path('', include(router.urls)),

    #profile
    path('request-profile-share/', profile_share_actions.as_view(), name='request_profile_share'),
    path('submit-profile-review/', submit_profile_review.as_view(), name='submit-profile-review'),
    
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/<uuid:user_id>/', UserProfileView.as_view(), name='user-profile-by-id'),
    path('search-profiles/', UserSearchFilterView.as_view(), name='search-profiles'),

    # Updated subscription endpoints

    path('paymaya/subscribe/',CreateSubscriptionPayment.as_view ()),
    path('paymaya/retry/', RetrySubscriptionPayment.as_view()),
    path('paymaya/webhook/', PayMayaWebhook.as_view()),

    # Verification endpoints
    path('upload-verification-document/', UploadVerificationDocumentView.as_view(), name='upload-verification-document'),
    path('request-mobile-verification/', RequestMobileVerificationView.as_view(), name='request-mobile-verification'),
    path('verify-mobile-otp/', VerifyMobileOTPView.as_view(), name='verify-mobile-otp'),
    path('verification-status/', GetVerificationStatusView.as_view(), name='verification-status'),
    path('admin/document-approval-webhook/', admin_document_approval_webhook.as_view(), name='admin-document-approval-webhook'),

    path('account-settings/', AccountSettingsView.as_view(), name='account-settings'),
    path('media/<path:path>', serve_media, name='serve_media'),
    path('file/<path:path>', BlobMediaView.as_view(), name='file_media'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

