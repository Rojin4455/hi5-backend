from rest_framework import serializers
from accounts.models import User
from theater_managemant.models import Theater

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True,required=True,style={'input_type':'password'})

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email:
            raise serializers.ValidationError("email is required")
        if not password:
            raise serializers.ValidationError("password is required")
        
        return data
    


class TheaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theater
        fields = '__all__'

class OwnerDetailsSerializer(serializers.ModelSerializer):
    theaters = TheaterSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = '__all__'