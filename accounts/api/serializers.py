from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import CustomUser, Profile
from accounts.utils import OTPManager

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
    
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        otp = data.get('otp')
        otp = int(otp)
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email")
        
        if not OTPManager.verify_otp(user, otp):
            raise serializers.ValidationError("Invalid OTP")

        return {'user': user}
    
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email address is not associated with any account.")
        return value

    def save(self):
        email = self.validated_data['email']
        user = CustomUser.objects.get(email=email)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        print(f"{uid}\n{token}")
        
        # password_reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"

        try:
            send_mail(
                'Password Reset Request',
                f'Click the link below to reset your password:\n',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            # logger.info(f'Password reset email sent to {email}')
        except Exception as e:
            # logger.error(f'Error sending password reset email: {str(e)}')
            raise serializers.ValidationError('Failed to send password reset email. Please try again later.')

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    uid = serializers.CharField()
    token = serializers.CharField()

    def validate(self, data):
        try:
            uid = data.get('uid')
            token = data.get('token')
            user_id = urlsafe_base64_decode(uid).decode()
            user = CustomUser.objects.get(pk=user_id)
            
            if not default_token_generator.check_token(user, token):
                raise serializers.ValidationError('Invalid token')

            if user.check_password(data.get('new_password')):
                raise serializers.ValidationError('The new password cannot be the same as the old password.')

            data['user'] = user
            return data
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            raise serializers.ValidationError('Invalid reset link')

    def save(self):
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()        
