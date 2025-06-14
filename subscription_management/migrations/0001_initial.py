# Generated by Django 5.1 on 2025-05-18 12:22

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Merchant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('contact_email', models.EmailField(max_length=254)),
                ('contact_phone', models.CharField(max_length=20)),
                ('agreement_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('campaign_start_date', models.DateTimeField()),
                ('campaign_end_date', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('monthly_movie_limit', models.IntegerField()),
                ('valid_days', models.JSONField(default=list)),
                ('daily_ticket_limit', models.IntegerField()),
                ('max_discount_per_ticket', models.DecimalField(decimal_places=2, max_digits=10)),
                ('max_ticket_price_coverage', models.DecimalField(decimal_places=2, default=200.0, max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True)),
                ('discount_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('description', models.TextField()),
                ('valid_from', models.DateTimeField()),
                ('valid_until', models.DateTimeField()),
                ('max_redemptions', models.IntegerField(default=100)),
                ('current_redemptions', models.IntegerField(default=0)),
                ('merchant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coupons', to='subscription_management.merchant')),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscription_id', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('start_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('end_date', models.DateTimeField()),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('EXPIRED', 'Expired'), ('CANCELLED', 'Cancelled')], default='ACTIVE', max_length=20)),
                ('payment_id', models.CharField(blank=True, max_length=255, null=True)),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='subscription_management.plan')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserCoupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('AVAILABLE', 'Available'), ('REDEEMED', 'Redeemed'), ('EXPIRED', 'Expired')], default='AVAILABLE', max_length=20)),
                ('assigned_date', models.DateTimeField(auto_now_add=True)),
                ('redemption_date', models.DateTimeField(blank=True, null=True)),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_coupons', to='subscription_management.coupon')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_coupons', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'coupon')},
            },
        ),
    ]
