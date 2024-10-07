from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from ..signals import send_otp_email
from rest_framework.decorators import action
from .serializers import (
    PasswordResetConfirmSerializer, PasswordResetSerializer, RegistrationSerializer, LoginSerializer, CompleteProfileUpdateSerializer, 
    ProfileSerializer, ProfileUpdateSerializer
)

class UserManagementViewSet(ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User registered successfully.",
                "user": user
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # refresh = RefreshToken.for_user(user)
            send_otp_email(user)
            return Response({
                'message': "OTP was sent, check your email",
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get', 'put'], url_path='update-profile', permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        if request.method == 'GET':
            serializer = ProfileUpdateSerializer(request.user)
            profile_serializer = ProfileSerializer(request.user.profile)
            return Response({
                "user": serializer.data,
                "profile": profile_serializer.data
            }, status=status.HTTP_200_OK)
        elif request.method == 'PUT':
            serializer = CompleteProfileUpdateSerializer(instance=request.user, data=request.data, partial=True)
            if serializer.is_valid():
                updated_user = serializer.save()
                return Response({
                    "message": "Profile updated successfully.",
                    "user": ProfileUpdateSerializer(updated_user).data,
                    "profile": ProfileSerializer(updated_user.profile).data
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='password-reset')
    def password_reset(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Password reset email sent'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='password-reset-confirm')
    def password_reset_confirm(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Password has been reset'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
