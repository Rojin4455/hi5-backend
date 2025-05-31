
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from dateutil.relativedelta import relativedelta
import stripe
from subscription_management.models import Plan, UserCoupon, Coupon, Subscription
from .serializers import PlanSerializer
from django.conf import settings
from datetime import timedelta
from rest_framework.views import APIView
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import HttpResponseRedirect


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer





stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(APIView):
    """
    Create a Stripe checkout session for subscription
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            plan_id = request.data.get('plan_id')
            
            # Get the plan details from the database
            try:
                plan = Plan.objects.get(id=plan_id, is_active=True)
            except Plan.DoesNotExist:
                return Response({"error": "Plan not found or inactive"}, status=status.HTTP_404_NOT_FOUND)
            

            previous_subscription = Subscription.objects.filter(user=request.user, status="INACTIVE").first()

            if previous_subscription and previous_subscription.plan and previous_subscription.plan.price < plan.price:
                price_difference =  plan.price - previous_subscription.plan.price
                amount = int(price_difference * 100)
            else:
                amount = int(plan.price * 100)

            subscription = Subscription.objects.create(
                user = request.user,
                plan = plan,
                status="INACTIVE",
            )

            print("amounttttttt: ", amount)
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'inr',
                            'product_data': {
                                'name': f'MoviePass - {plan.name} Subscription',
                                'description': f'Monthly movie limit: {plan.monthly_movie_limit}, Daily ticket limit: {plan.daily_ticket_limit}'
                            },
                            'unit_amount': amount,
                        },
                        'quantity': 1,
                    },
                ],
                metadata={
                    'plan_id': plan.id,
                    'user_id': request.user.id,
                },
                mode='payment',
                success_url=f"{settings.BASE_API_URL}/subscription/payment-success/{subscription.id}/{previous_subscription.id}/?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.BASE_API_URL}/subscription/payment-failed",
            )

            subscription.payment_id = checkout_session.id
            subscription.save()
            
            return Response({'id': checkout_session.id})
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VerifySubscriptionView(APIView):
    """
    Verify the subscription after successful payment
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            session_id = request.data.get('session_id')
            
            # Retrieve the checkout session to verify payment
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                # Get plan and user from metadata
                plan_id = session.metadata.get('plan_id')
                
                plan = Plan.objects.get(id=plan_id)
                
                # Calculate end date (30 days from now)
                end_date = timezone.now() + timedelta(days=30)
                
                # Create subscription
                subscription = Subscription.objects.create(
                    user=request.user,
                    plan=plan,
                    start_date=timezone.now(),
                    end_date=end_date,
                    status='ACTIVE',
                    payment_id=session.payment_intent
                )
                
                # Return subscription details
                return Response({
                    'id': subscription.id,
                    'plan': plan.name,
                    'start_date': subscription.start_date,
                    'end_date': subscription.end_date,
                    'status': subscription.status
                })
            else:
                return Response({'error': 'Payment not completed'}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def stripe_webhook(request):
    """
    Webhook to handle Stripe events
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Process subscription
        if session.payment_status == 'paid':
            # Get plan and user from metadata
            plan_id = session.metadata.get('plan_id')
            user_id = session.metadata.get('user_id')
            
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                plan = Plan.objects.get(id=plan_id)
                user = User.objects.get(id=user_id)
                
                # Calculate end date (30 days from now)
                end_date = timezone.now() + timedelta(days=30)
                
                # Check if there's an existing active subscription
                existing_subscription = Subscription.objects.filter(
                    user=user,
                    status='ACTIVE'
                ).first()
                
                if existing_subscription:
                    # Update existing subscription end date
                    existing_subscription.end_date = end_date
                    existing_subscription.payment_id = session.payment_intent
                    existing_subscription.save()
                else:
                    # Create new subscription
                    Subscription.objects.create(
                        user=user,
                        plan=plan,
                        start_date=timezone.now(),
                        end_date=end_date,
                        status='ACTIVE',
                        payment_id=session.payment_intent
                    )
            except Exception as e:
                print(f"Error processing webhook: {str(e)}")
                
    return HttpResponse(status=200)





from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer

class PlanListView(APIView):
    """
    List all active subscription plans
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        plans = Plan.objects.filter(is_active=True)
        serializer = PlanSerializer(plans, many=True)
        return Response(serializer.data)

class ActiveSubscriptionView(APIView):
    """
    Get the user's active subscription if any
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        subscription = Subscription.objects.filter(
            user=request.user,
            status='ACTIVE',
            end_date__gt=timezone.now()
        ).first()

        print("subsctioption ;", Subscription.objects.all())
        
        if subscription:
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data)
        else:
            return Response({"detail": "No active subscription found"}, status=status.HTTP_404_NOT_FOUND)
        



class PaymentSuccessClass(APIView):
    permission_classes = []
    def get(self, request, subscription_id, prev_subscription_id):
        try:
            subscription = Subscription.objects.get(id=subscription_id)
            prev_subscription = Subscription.objects.get(id=prev_subscription_id)
            prev_subscription.status = "INACTIVE"
            prev_subscription.save()
            if subscription.status == 'ACTIVE':
                return HttpResponseRedirect(f"{settings.BASE_APP_URL}/user/subscription-success?id={subscription.id}")
        
            if not subscription.payment_id:
                return HttpResponseRedirect(f"{settings.BASE_APP_URL}/user/subscription-error?message=Checkout Session ID missing")
            
            session = stripe.checkout.Session.retrieve(subscription.payment_id)

            if session['payment_status'] == 'paid':
                subscription.status = 'ACTIVE'
                subscription.save()
                return HttpResponseRedirect(f"{settings.BASE_APP_URL}/profile?success_subscription_id={subscription.id}")


        except Subscription.DoesNotExist:
            return HttpResponseRedirect(f"{settings.BASE_APP_URL}/user/subscription-error?message=subscription+not+found")
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)