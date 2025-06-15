from rest_framework import status
from rest_framework.response import Response
from accounts.models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from ..signals import send_otp_email
from rest_framework.decorators import action
from .serializers import (
    PasswordChangeSerializer, PasswordResetConfirmSerializer, PasswordResetSerializer, RegistrationSerializer, LoginSerializer,
    TokenSerializer, UserProfileUpdateSerializer, VerifyOTPSerializer, AddAdminSerializer
)

class UserManagementViewSet(ViewSet):
    permission_classes = [AllowAny]
    queryset = CustomUser.objects.all()

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

    @action(detail=False, methods=['get'], url_path='all-users', permission_classes=[IsAdminUser])
    def all_users(self, request):
        """Get all users."""
        users = self.queryset.all()
        serializer = UserProfileUpdateSerializer(users, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

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
        # Determine which user's profile to update
        target_user_id = request.query_params.get('user_id')
        is_admin = request.user.role == 'Administrator'
        
        if target_user_id and is_admin:
            try:
                target_user = CustomUser.objects.get(id=target_user_id)
            except CustomUser.DoesNotExist:
                return Response({"error": f"User {target_user_id} not found."}, 
                            status=status.HTTP_404_NOT_FOUND)
        elif target_user_id and not is_admin:
            return Response(
                {"error": "You don't have permission to update other users' profiles."},
                status=status.HTTP_403_FORBIDDEN
            )
        else:
            target_user = request.user
        
        if request.method == 'GET':
            serializer = UserProfileUpdateSerializer(
                target_user, 
                context={'request': request}
            )
            return Response(serializer.data)

        elif request.method == 'PUT' or request.method == 'PATCH':
            # Handle the profile update
            serializer = UserProfileUpdateSerializer(
                target_user,
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
        return Response({'detail': 'Password reset email not sent'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='password-reset-confirm')
    def password_reset_confirm(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Password has been reset'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        """Change user's password."""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='add-admin', permission_classes=[IsAuthenticated])
    def add_admin(self, request):
        """Allow a superuser to add a new administrator."""
        if not request.user.is_superuser:
            return Response(
                {"error": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AddAdminSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Administrator added successfully.",
                "user": UserProfileUpdateSerializer(user, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='change-role', permission_classes=[IsAuthenticated])
    def change_role(self, request):
        """Change user's role.
        
        Only administrators are allowed to change roles.
        """
        # Check if the requesting user is an administrator
        if not request.user.is_superuser:
            return Response(
                {"error": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        user_id = request.data.get('user_id')
        new_role = request.data.get('new_role')
        
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": f"User {user_id} not found."}, status=status.HTTP_404_NOT_FOUND)
            
        # If new_role is provided, use it directly
        if new_role:
            if new_role not in ['Customer', 'Administrator']:
                return Response(
                    {"error": "Invalid role. Must be 'Customer' or 'Administrator'."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.role = new_role
            
        else:
            
            if user.role == 'Administrator':
                user.role = 'Customer'
            else:
                user.role = 'Administrator'
        
        if user.role == 'Administrator':
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = False
            user.is_superuser = False
            
        user.save()
        
        return Response({
            "message": "User role changed successfully.", 
            "user_id": user_id,
            "new_role": user.role
        }, status=status.HTTP_200_OK)