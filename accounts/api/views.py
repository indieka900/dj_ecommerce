from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from ..signals import send_otp_email
from rest_framework.decorators import action
from .serializers import (
    PasswordResetConfirmSerializer, PasswordResetSerializer, RegistrationSerializer, LoginSerializer,
    TokenSerializer, UserProfileUpdateSerializer, VerifyOTPSerializer
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
                "user": UserProfileUpdateSerializer(user, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='login')
    def login_user(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            # send_otp_email(user)
            return Response({
                'refresh': str(refresh),
                'access': str(access),
                "user": UserProfileUpdateSerializer(user, context={'request': request}).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='verify-otp')
    def verify_otp(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        token_data = {
            'refresh': str(refresh),
            'access': str(access),
            'user_role': user.role,
        }
        token_serializer = TokenSerializer(token_data)

        return Response(token_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get', 'put'], url_path='profile', permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        if request.method == 'GET':
            serializer = UserProfileUpdateSerializer(
                request.user, 
                context={'request': request}
            )
            return Response(serializer.data)

        elif request.method == 'PUT' or request.method == 'PATCH':
            # Handle the profile update
            """Update current user's profile information."""
            serializer = UserProfileUpdateSerializer(
                request.user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "message": "Profile updated successfully.",
                    "user": serializer.data
                })
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
