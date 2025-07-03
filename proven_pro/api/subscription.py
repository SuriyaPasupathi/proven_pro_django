# views.py

import uuid
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import PlanDetails, UserSubscription
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone

class CreateSubscriptionPayment(APIView):
    def post(self, request):
        user = request.user.id
        plan_name = request.data.get("plan")
        plan = PlanDetails.objects.filter(name=plan_name).first()

        if not plan:
            return Response({"error": "Invalid plan"}, status=400)

        reference = str(uuid.uuid4())

        UserSubscription.objects.create(
            user=user, plan=plan, status='pending', request_reference=reference
        )

        payload = {
            "totalAmount": {
                "value": str(plan.price),
                "currency": "PHP",
                "details": {"subtotal": str(plan.price)}
            },
            "buyer": {
                "firstName": user.first_name,
                "lastName": user.last_name,
                "contact": {
                    "phone": user.phone,
                    "email": user.email,
                }
            },
            "redirectUrl": {
                "success": f"https://yourdomain.com/payment/success?ref={reference}",
                "failure": f"https://yourdomain.com/payment/failure?ref={reference}",
                "cancel": f"https://yourdomain.com/payment/cancel?ref={reference}",
            },
            "requestReferenceNumber": reference
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {settings.PAYMAYA_PUBLIC_KEY}"
        }

        response = requests.post(
            f"{settings.PAYMAYA_API_URL}/checkout/v1/checkouts",
            headers=headers, json=payload
        )

        if response.status_code == 200:
            return Response({
                "checkout_url": response.json()["redirectUrl"],
                "reference": reference
            })
        else:
            return Response(response.json(), status=response.status_code)

class RetrySubscriptionPayment(APIView):
    def post(self, request):
        reference = request.data.get("reference")
        sub = UserSubscription.objects.filter(request_reference=reference, status='failed').first()

        if not sub:
            return Response({"error": "No failed transaction found"}, status=404)

        request.data["plan"] = sub.plan.name
        return CreateSubscriptionPayment().post(request)


class PayMayaWebhook(APIView):
    def post(self, request):
        data = request.data
        ref = data.get("requestReferenceNumber")
        status_text = data.get("paymentStatus", "").lower()

        sub = UserSubscription.objects.filter(request_reference=ref).first()
        if sub:
            if "success" in status_text:
                sub.status = "paid"
            elif "failed" in status_text:
                sub.status = "failed"
            sub.save()
        return Response(status=200)
    
class SubscriptionCheck(APIView):
    def get(self, request):
        user = request.user
        subscription = UserSubscription.objects.filter(user=user).first()

        if not subscription:
            return Response({"status": "no_subscription"}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "status": subscription.status,
            "plan": subscription.plan.name,
            "created_at": subscription.created_at.isoformat()
        }, status=status.HTTP_200_OK)
    

class SubscribePlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan = request.data.get('plan')  # expects: 'free', 'standard', or 'premium'

        if plan not in ['free', 'standard', 'premium']:
            return Response({'error': 'Invalid subscription plan'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.subscription_type = plan
        user.subscription_active = True
        user.subscription_start_date = timezone.now()
        user.subscription_end_date = timezone.now() + timezone.timedelta(days=30)
        user.save()

        return Response({'message': f'Subscribed to {plan.capitalize()} Plan'}, status=status.HTTP_200_OK)