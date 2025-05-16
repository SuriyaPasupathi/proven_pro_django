from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
from django.utils import timezone
import requests
from django.contrib.auth import get_user_model

User = get_user_model()


class UpdateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Update user's subscription type
        """
        subscription_type = request.data.get('subscription_type')
        
        if subscription_type not in ['free', 'standard', 'premium']:
            return Response(
                {'message': 'Invalid subscription type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        user.subscription_type = subscription_type
        user.save()
        
        return Response({
            'message': 'Subscription updated successfully',
            'has_profile': True
        })


class CreateGCashPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            subscription_type = request.data.get('subscription_type')
            
            # Get price based on subscription type (in USD cents)
            # Standard: $10 USD = 1000 cents
            # Premium: $20 USD = 2000 cents
            if subscription_type == 'standard':
                price = 100 # $10.00 in cents
                plan_name = "Standard Plan"
            elif subscription_type == 'premium':
                price = 200  # $20.00 in cents
                plan_name = "Premium Plan"
            else:
                return Response(
                    {'error': 'Invalid subscription type. Must be "standard" or "premium"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create PayMongo source for GCash
            import base64
            import requests
            import uuid
            
            paymongo_url = "https://api.paymongo.com/v1/sources"
            auth_string = f"{settings.PAYMONGO_SECRET_KEY}:"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_auth}",
                "Content-Type": "application/json"
            }
            
            # Convert USD to PHP (approximate conversion for demonstration)
            # In production, you should use a currency conversion API
            # PayMongo requires amount in smallest currency unit (centavos for PHP)
            php_amount = int(price * 84)  # Approximate USD to PHP conversion
            
            # Generate a unique reference number
            reference_number = f"PROVENPRO-{uuid.uuid4().hex[:8].upper()}"
            
            # Ensure we have valid billing information
            user = request.user
            billing_name = f"{user.first_name} {user.last_name}".strip()
            if not billing_name:
                billing_name = user.username or "Customer"
                
            billing_email = user.email
            if not billing_email:
                billing_email = "customer@example.com"
            
            # Fix: Flatten metadata - no nested objects
            payload = {
                "data": {
                    "attributes": {
                        "amount": php_amount,
                        "redirect": {
                            "success": f"{settings.FRONTEND_URL}/subscription/success",
                            "failed": f"{settings.FRONTEND_URL}/subscription/failed"
                        },
                        "type": "gcash",
                        "currency": "PHP",
                        "description": f"{plan_name} - ${price/100} USD",
                        "billing": {
                            "name": billing_name,
                            "email": billing_email
                        },
                        "metadata": {
                            "user_id": str(user.id),
                            "subscription_type": subscription_type,
                            "reference_number": reference_number,
                            "plan_name": plan_name,
                            "usd_amount": str(price/100)  # Convert to string to avoid nested objects
                        }
                    }
                }
            }
            
            # Debug information
            print(f"PayMongo URL: {paymongo_url}")
            print(f"Headers: {headers}")
            print(f"Payload: {payload}")
            
            response = requests.post(paymongo_url, json=payload, headers=headers)
            
            # Debug response
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}")
            
            if response.status_code != 200:
                return Response(
                    {'error': 'Failed to create payment source', 'details': response.json()},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            source_data = response.json()['data']
            source_id = source_data['id']
            checkout_url = source_data['attributes']['redirect']['checkout_url']
            
            return Response({
                'checkoutUrl': checkout_url,
                'sourceId': source_id,
                'referenceNumber': reference_number,
                'amount': price/100,  # Return amount in USD
                'currency': 'USD',
                'planName': plan_name
            })
                
        except Exception as e:
            import traceback
            print(f"Exception: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GCashWebhookView(APIView):
    permission_classes = []  # No authentication for webhooks
    
    def post(self, request):
        payload = request.data
        
        # Log the webhook data for debugging
        print(f"Received GCash webhook: {payload}")
        
        # Process the payment notification
        transaction_id = payload.get('data', {}).get('id')
        attributes = payload.get('data', {}).get('attributes', {})
        status_value = attributes.get('status')
        metadata = attributes.get('metadata', {})
        
        user_id = metadata.get('user_id')
        subscription_type = metadata.get('subscription_type')
        
        if status_value == 'paid':
            # Update user subscription
            try:
                user = User.objects.get(id=user_id)
                
                # Update user with subscription
                user.subscription_type = subscription_type
                user.subscription_active = True
                user.subscription_start_date = timezone.now()
                user.subscription_end_date = timezone.now() + timezone.timedelta(days=30)
                user.save()
                
                print(f"Updated subscription for user {user_id} to {subscription_type}")
                return Response({'status': 'success'})
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=400)
        
        return Response({'status': 'received'})




class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        source_id = request.data.get('source_id')
        subscription_type = request.data.get('subscription_type')
        
        # Debug prints
        print(f"Verifying payment for source_id: {source_id}")
        print(f"Subscription type from request: {subscription_type}")
        
        if not source_id:
            return Response({'success': False, 'error': 'Missing source ID'}, status=400)
            
        try:
            # Verify payment status with PayMongo
            import base64
            import requests
            
            paymongo_url = f"https://api.paymongo.com/v1/sources/{source_id}"
            auth_string = f"{settings.PAYMONGO_SECRET_KEY}:"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_auth}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(paymongo_url, headers=headers)
            
            if response.status_code != 200:
                return Response({'success': False, 'error': 'Failed to verify payment'}, status=500)
                
            source_data = response.json()['data']
            source_status = source_data['attributes']['status']
            metadata = source_data['attributes']['metadata']
            
            # Get subscription type from metadata if not provided in request
            if not subscription_type:
                subscription_type = metadata.get('subscription_type')
            
            print(f"Source status: {source_status}")
            print(f"Using subscription type: {subscription_type}")
            
            # Check if this source is for the current user
            if str(request.user.id) != metadata.get('user_id'):
                return Response({'success': False, 'error': 'Unauthorized'}, status=403)
            
            if source_status in ['chargeable', 'paid']:
                # Source is valid, update user subscription
                user = request.user
                user.subscription_type = subscription_type
                user.subscription_active = True
                user.subscription_start_date = timezone.now()
                user.subscription_end_date = timezone.now() + timezone.timedelta(days=30)
                user.save()
                
                print(f"Updated user subscription to: {user.subscription_type}")
                
                return Response({
                    'success': True, 
                    'status': 'activated',
                    'subscription_type': subscription_type,
                    'has_profile': True
                })
            else:
                # Payment still pending
                return Response({'success': False, 'status': source_status})
                
        except Exception as e:
            import traceback
            print(f"Verification error: {str(e)}")
            print(traceback.format_exc())
            return Response({'success': False, 'error': str(e)}, status=500)

class VerifySubscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        source_id = request.data.get('source_id')
        
        if not source_id:
            return Response({'success': False, 'error': 'Missing source ID'}, status=400)
            
        try:
            # Verify source status with PayMongo
            import base64
            import requests
            
            paymongo_url = f"https://api.paymongo.com/v1/sources/{source_id}"
            auth_string = f"{settings.PAYMONGO_SECRET_KEY}:"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_auth}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(paymongo_url, headers=headers)
            
            if response.status_code != 200:
                return Response({'success': False, 'error': 'Failed to verify source'}, status=500)
                
            source_data = response.json()['data']
            source_status = source_data['attributes']['status']
            metadata = source_data['attributes']['metadata']
            
            if source_status == 'chargeable' or source_status == 'paid':
                # Source is valid, update user subscription if not already done
                subscription_type = metadata.get('subscription_type')
                
                # Check if user already has an active subscription
                user = request.user
                if user.subscription_active:
                    # Already activated
                    return Response({'success': True, 'status': 'already_active'})
                
                # Update user subscription
                user.subscription_type = subscription_type
                user.subscription_active = True
                user.subscription_start_date = timezone.now()
                user.subscription_end_date = timezone.now() + timezone.timedelta(days=30)
                user.save()
                
                return Response({'success': True, 'status': 'activated'})
            else:
                # Payment still pending
                return Response({'success': False, 'status': source_status})
                
        except Exception as e:
            import traceback
            print(f"Verification error: {str(e)}")
            print(traceback.format_exc())
            return Response({'success': False, 'error': str(e)}, status=500)

class PayMongoWebhookView(APIView):
    permission_classes = []  # No authentication for webhooks
    
    def post(self, request):
        try:
            payload = request.data
            event_data = payload.get('data', {})
            event_type = payload.get('type')
            
            # Log the webhook event
            print(f"Received PayMongo webhook: {event_type}")
            print(f"Payload: {payload}")
            
            # Process payment success event
            if event_type == 'source.chargeable':
                attributes = event_data.get('attributes', {})
                metadata = attributes.get('metadata', {})
                
                user_id = metadata.get('user_id')
                subscription_type = metadata.get('subscription_type')
                
                if not user_id or not subscription_type:
                    return Response({'error': 'Missing user_id or subscription_type in metadata'}, status=400)
                
                # Update user subscription immediately
                try:
                    user = User.objects.get(id=user_id)
                    user.subscription_type = subscription_type
                    user.subscription_active = True
                    user.subscription_start_date = timezone.now()
                    user.subscription_end_date = timezone.now() + timezone.timedelta(days=30)
                    user.save()
                    print(f"Updated subscription for user {user_id} to {subscription_type}")
                except User.DoesNotExist:
                    print(f"User {user_id} not found")
            
            return Response({'status': 'success'})
            
        except Exception as e:
            import traceback
            print(f"PayMongo webhook error: {str(e)}")
            print(traceback.format_exc())
            return Response({'error': str(e)}, status=500)

class SubscriptionCheckView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Check user's subscription status
        """
        try:
            user = request.user
            
            # Get subscription details
            subscription_type = user.subscription_type
            subscription_active = user.subscription_active
            
            # Get plan details based on subscription type
            plan_details = {
                'free': {'name': 'Free Plan', 'price': 0},
                'standard': {'name': 'Standard Plan', 'price': 10},
                'premium': {'name': 'Premium Plan', 'price': 20}
            }
            
            plan = plan_details.get(subscription_type, {'name': 'Unknown', 'price': 0})
            
            return Response({
                'subscription_type': subscription_type,
                'subscription_active': subscription_active,
                'plan_name': plan['name'],
                'plan_price': plan['price'],
                'has_profile': True
            })
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
