from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from ..signals import send_otp_email
from rest_framework.decorators import action
from .serializers import (
    RegistrationSerializer, LoginSerializer, CompleteProfileUpdateSerializer, 
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
                "user_id": user.id
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

    @action(detail=False, methods=['put'], url_path='update-profile', permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        serializer = CompleteProfileUpdateSerializer(instance=request.user, data=request.data, partial=True)
        if serializer.is_valid():
            updated_user = serializer.save()
            return Response({
                "message": "Profile updated successfully.",
                "user": ProfileUpdateSerializer(updated_user).data,
                "profile": ProfileSerializer(updated_user.profile).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)