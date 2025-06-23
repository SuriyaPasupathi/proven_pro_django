import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from .models import Users
from rest_framework.permissions import IsAuthenticated

# Helper: Get Maya headers
def get_maya_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Basic {settings.MAYA_SECRET_KEY}"
    }

# 1. Create Maya Subscription (initiate payment)
class CreateMayaSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan = request.data.get('plan')  # 'standard' or 'premium'
        if plan not in ['standard', 'premium']:
            return Response({'error': 'Invalid plan'}, status=400)

        # Set amount based on plan
        amount = 499 if plan == 'standard' else 999  # Example: 499/999 PHP

        payload = {
            "totalAmount": {
                "value": amount,
                "currency": "PHP"
            },
            "buyer": {
                "firstName": request.user.first_name,
                "lastName": request.user.last_name,
                "contact": {
                    "email": request.user.email
                }
            },
            "redirectUrl": {
                "success": "https://your-frontend.com/payment-success",
                "failure": "https://your-frontend.com/payment-failed",
                "cancel": "https://your-frontend.com/payment-cancelled"
            },
            "requestReferenceNumber": f"{request.user.id}-{timezone.now().timestamp()}",
            "items": [
                {
                    "name": f"{plan.capitalize()} Subscription",
                    "quantity": 1,
                    "totalAmount": {
                        "value": amount,
                        "currency": "PHP"
                    }
                }
            ]
        }

        response = requests.post(
            settings.MAYA_API_URL,
            json=payload,
            headers=get_maya_headers()
        )

        if response.status_code == 200:
            checkout_data = response.json()
            return Response({
                "checkout_id": checkout_data.get("checkoutId"),
                "redirect_url": checkout_data.get("redirectUrl")
            })
        else:
            return Response({"error": "Failed to create Maya checkout", "details": response.text}, status=400)

# 2. Verify Maya Payment (manual check)
class VerifyMayaPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        checkout_id = request.data.get('checkout_id')
        if not checkout_id:
            return Response({'error': 'Missing checkout_id'}, status=400)

        url = f"https://pg-sandbox.paymaya.com/checkout/v1/checkouts/{checkout_id}"
        response = requests.get(url, headers=get_maya_headers())

        if response.status_code == 200:
            data = response.json()
            status_ = data.get('status')
            if status_ == 'COMPLETED':
                # Update user subscription
                plan = data['items'][0]['name'].split()[0].lower()
                user = request.user
                user.subscription_type = plan
                user.subscription_active = True
                user.subscription_start_date = timezone.now()
                user.subscription_end_date = timezone.now() + timezone.timedelta(days=30)
                user.save()
                return Response({'status': 'success', 'plan': plan})
            else:
                return Response({'status': status_})
        else:
            return Response({'error': 'Failed to verify payment', 'details': response.text}, status=400)

# 3. Retry Maya Payment (re-initiate checkout)
class RetryMayaPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Just call the create endpoint again with the same plan
        plan = request.data.get('plan')
        return CreateMayaSubscriptionView().post(request)

# 4. Maya Webhook (for automatic payment status update)
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class MayaWebhookView(APIView):
    permission_classes = []

    def post(self, request):
        data = request.data
        # You may want to log or verify the webhook signature here
        if data.get('status') == 'COMPLETED':
            # Find user by reference number or email
            ref = data.get('requestReferenceNumber')
            user_id = ref.split('-')[0]
            try:
                user = Users.objects.get(id=user_id)
                plan = data['items'][0]['name'].split()[0].lower()
                user.subscription_type = plan
                user.subscription_active = True
                user.subscription_start_date = timezone.now()
                user.subscription_end_date = timezone.now() + timezone.timedelta(days=30)
                user.save()
            except Users.DoesNotExist:
                pass
        return Response({'status': 'received'})
