from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .auth_user import (
    RegisterViewSet, LoginView, google_auth, RequestResetPasswordView, 
    PasswordResetConfirmView, LogoutView
)
from .subscription import(
    SubscriptionCheckView,
    UpdateSubscriptionView,CreateGCashPaymentView,VerifyPaymentView,PayMongoWebhookView,GCashWebhookView)

from .views import ( 
    UserProfileView,
    generate_profile_share,
    verify_profile_share,
    submit_review,
    get_reviews,
    UploadVerificationDocumentView,
    RequestMobileVerificationView,
    VerifyMobileOTPView,
    GetVerificationStatusView,
    admin_document_approval_webhook,
    UserSearchFilterView,
    health_check,
    CheckProfileStatusView, 
)

router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='otp')
# router.register(r'reviews', ReviewViewSet)

urlpatterns = [
    path('health_check', health_check, name='health_check'),
    #auth
    path('google-auth/', google_auth, name='google-auth'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile_status/', CheckProfileStatusView.as_view(), name='profile-status'),
    path('request-reset-password/', RequestResetPasswordView.as_view(), name='request-reset-password'),
    path('reset-password-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Include router URLs
    path('', include(router.urls)),

    #profile
    path('share-profile/', generate_profile_share, name='share-profile'),
    path('verify-share/<uuid:token>/', verify_profile_share, name='verify-share'),
    path('submit-review/<uuid:token>/', submit_review, name='submit-review'),
    path('get_reviews/', get_reviews, name='get_reviews'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('search-profiles/', UserSearchFilterView.as_view(), name='search-profiles'),

    # Updated subscription endpoints
    path('update-subscription/', UpdateSubscriptionView.as_view(), name='update-subscription'),
    # path('create-payment-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    
    path('create-gcash-payment/', CreateGCashPaymentView.as_view(), name='create-gcash-payment'),
    path('gcash-webhook/', GCashWebhookView.as_view(), name='gcash-webhook'),
    path('verify-payment/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('paymongo-webhook/', PayMongoWebhookView.as_view(), name='paymongo-webhook'),
    path('subscription-check/', SubscriptionCheckView.as_view(), name='subscription-check'),
    path('profiles/<uuid:token>/', verify_profile_share, name='verify-share'),

    # Verification endpoints
    path('upload-verification-document/', UploadVerificationDocumentView.as_view(), name='upload-verification-document'),
    path('request-mobile-verification/', RequestMobileVerificationView.as_view(), name='request-mobile-verification'),
    path('verify-mobile-otp/', VerifyMobileOTPView.as_view(), name='verify-mobile-otp'),
    path('verification-status/', GetVerificationStatusView.as_view(), name='verification-status'),
    path('admin/document-approval-webhook/', admin_document_approval_webhook, name='admin-document-approval-webhook'),
]

# Add this at the end to serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
