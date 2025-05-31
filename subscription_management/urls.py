from django.urls import path
from .views import (
    CreateCheckoutSessionView, 
    VerifySubscriptionView, 
    stripe_webhook,
    PlanListView,
    ActiveSubscriptionView,
    PaymentSuccessClass
)

urlpatterns = [
    path('create-checkout-session/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('verify-subscription/', VerifySubscriptionView.as_view(), name='verify-subscription'),
    path('payment-success/<int:subscription_id>/<int:prev_subscription_id>/', PaymentSuccessClass.as_view(), name='verify-subscription'),
    path('payment-failed/', VerifySubscriptionView.as_view(), name='verify-subscription'),
    path('webhook/', stripe_webhook, name='stripe-webhook'),
    path('plans/', PlanListView.as_view(), name='plan-list'),
    path('active/', ActiveSubscriptionView.as_view(), name='active-subscription'),
]