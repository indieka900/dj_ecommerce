from rest_framework import serializers
from django.contrib.auth import authenticate
from accounts.models import CustomUser, Profile

class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'password')

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            raise serializers.ValidationError("Both email and password are required.")
        
        user = authenticate(email=email, password=password)
        
        if not user:
            raise serializers.ValidationError("Unable to log in with provided credentials.")
        
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        
        data['user'] = user
        return data
class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'phone_number', 'role')

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('country', 'city', 'street_address', 'profile_picture')

class CompleteProfileUpdateSerializer(serializers.Serializer):
    user = ProfileUpdateSerializer()
    profile = ProfileSerializer()

    def update(self, instance, validated_data):
        user_data = validated_data.get('user', {})
        profile_data = validated_data.get('profile', {})

        # Update the User fields
        for attr, value in user_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update the Profile fields
        profile = instance.profile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()

        return instance