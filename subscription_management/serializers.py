from rest_framework import serializers
from .models import Plan, Subscription

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'price', 'monthly_movie_limit', 'valid_days', 
                 'daily_ticket_limit', 'max_discount_per_ticket', 'max_ticket_price_coverage']

class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer()
    
    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'subscription_id', 'start_date', 'end_date', 'status']