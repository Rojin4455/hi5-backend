from rest_framework import serializers
from accounts.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


class OwnerSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'phone', 'first_name', 'business_name']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        
        user = User.objects.create_user(
            email=validated_data.get('email'),
            password=validated_data.get('password'),
            phone=validated_data.get('phone'),
            first_name=validated_data.get('first_name'),
            business_name=validated_data.get('business_name'),
            is_owner = True

        )
        user.save()
        return user


class TheaterOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'email', 'phone', 'business_name', 'is_approved', 'date_joined']


class OwnerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        # Authenticate the user using Django's authenticate method
        print("email: ",email, "password: ", password)
        user = User.objects.get(email=email)
        print("user og: ",user)
        user = authenticate(email=email, password=password)
        print("userrrrrr: ",user)
        if user is None:
            raise serializers.ValidationError("Invalid login credentials")

        # Ensure the user is a theater owner and approved by admin
        if not user.is_owner:
            raise serializers.ValidationError("Only theater owners can log in.")
        
        if not user.is_approved:
            raise serializers.ValidationError("Your account is not yet approved by the admin.")

        data['user'] = user
        return data

    def get_tokens(self, user):
        # Generate JWT token for the user
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
