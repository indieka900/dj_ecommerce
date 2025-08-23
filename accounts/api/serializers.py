from rest_framework import serializers
from ecommerce.models import Order, OrderItem
from accounts.models import Address
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db import transaction
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import CustomUser, CustomerProfile
from accounts.utils import OTPManager

User = get_user_model()


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

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    country = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    city = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    street_address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role', 'phone_number',
            'country', 'city', 'street_address', 'profile_picture', 'is_active', 'is_staff', 'is_superuser'
        ]
        read_only_fields = ['email', 'role', 'is_active', 'is_staff', 'is_superuser']

    def to_representation(self, instance):
        """Add profile info to the representation."""
        representation = super().to_representation(instance)
        try:
            profile = instance.customerprofile_profile  # based on related_name
            representation.update({
                'country': profile.country,
                'city': profile.city,
                'street_address': profile.street_address,
                'profile_picture': self.context['request'].build_absolute_uri(profile.profile_picture.url) if profile.profile_picture else None,
            })
        except CustomerProfile.DoesNotExist:
            pass
        return representation

    @transaction.atomic
    def update(self, instance, validated_data):
        profile_fields = ['country', 'city', 'street_address', 'profile_picture']
        profile_data = {field: validated_data.pop(field) for field in profile_fields if field in validated_data}

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update or create profile
        profile, created = CustomerProfile.objects.get_or_create(user=instance)
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
        
        password_reset_url = f"{settings.FRONTEND_URL}reset-password/{uid}/{token}"

        try:
            send_mail(
                'Password Reset Request',
                f'Click the link below to reset your password:\n {password_reset_url}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            # logger.info(f'Password reset email sent to {email}')
        except Exception as e:
            # logger.error(f'Error sending password reset email: {str(e)}')
            raise serializers.ValidationError('Failed to send password reset email. Please try again later.')

class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New password fields didn't match."})
        return data
    
    
    
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
        
class TokenSerializer(serializers.Serializer):
    """
    Serializer for handling JWT tokens.
    """
    refresh = serializers.CharField()
    access = serializers.CharField()
    user_role = serializers.CharField()  
    
class AddAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('email', 'role')
        extra_kwargs = {
            'email': {'required': True},
            'role': {'read_only': True}
        }

    def create(self, validated_data):
        # Force the role to 'Administrator' regardless of input
        validated_data['role'] = 'Administrator'
        user = CustomUser.objects.create_user(**validated_data)
        user.is_staff = True
        user.save()

        self.send_password_setup_email(user)
        return user

    def send_password_setup_email(self, user):
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"{settings.FRONTEND_URL}reset-password/{uid}/{token}"

        try:
            send_mail(
                'Administrator Account Created',
                f'You have been added as an administrator.\nPlease set your password using the link below:\n{reset_url}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending password setup email: {str(e)}")
            raise serializers.ValidationError("Failed to send password setup email. Please try again.")


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'

class CustomerStatsSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_order_date = serializers.DateTimeField()
    avg_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)

class CustomerOrderSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    items = serializers.SerializerMethodField()
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'status_display', 
            'payment_status', 'payment_status_display', 'total',
            'created_at', 'updated_at', 'tracking_number', 'items'
        ]

    def get_items(self, obj):
        items = obj.items.all()
        return items.count()
class CustomerDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    orders = CustomerOrderSerializer(many=True, read_only=True)
    stats = serializers.SerializerMethodField()
    tier = serializers.SerializerMethodField()
    is_vip = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'is_active', 'date_joined', 'role',
            'orders', 'stats', 'tier', 'is_vip', 'last_activity'
        ]
    
    def get_full_name(self, obj):
        return f"{obj.first_name or ''} {obj.last_name or ''}".strip() or obj.email.split('@')[0]
    
    def get_stats(self, obj):
        orders = obj.orders.filter(payment_status='Paid')
        total_spent = orders.aggregate(total=Sum('total'))['total'] or 0
        total_orders = orders.count()
        # items = OrderItem.objects.filter(order__in=orders).count()
        last_order = orders.first()
        avg_order_value = total_spent / total_orders if total_orders > 0 else 0
        
        return {
            'total_orders': total_orders,
            'total_spent': total_spent,
            # 'items' : items,
            'last_order_date': last_order.created_at if last_order else None,
            'avg_order_value': avg_order_value
        }
    
    def get_tier(self, obj):
        total_spent = obj.orders.filter(payment_status='Paid').aggregate(
            total=Sum('total'))['total'] or 0
        
        if total_spent >= 30000:
            return 'Platinum'
        elif total_spent >= 10000:
            return 'Gold'
        elif total_spent >= 1000:
            return 'Silver'
        else:
            return 'Bronze'
    
    def get_is_vip(self, obj):
        total_spent = obj.orders.filter(payment_status='Paid').aggregate(
            total=Sum('total'))['total'] or 0
        return total_spent >= 30000
    
    def get_last_activity(self, obj):
        last_order = obj.orders.first()
        return last_order.created_at if last_order else obj.date_joined

class CustomerListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    tier = serializers.SerializerMethodField()
    is_vip = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'is_active', 'date_joined', 'role',
            'total_orders', 'total_spent', 'tier', 'is_vip',
            'last_activity', 'avatar'
        ]
    
    def get_full_name(self, obj):
        return f"{obj.first_name or ''} {obj.last_name or ''}".strip() or obj.email.split('@')[0]
    
    def get_total_orders(self, obj):
        return obj.orders.filter(payment_status='Paid').count()
    
    def get_total_spent(self, obj):
        return obj.orders.filter(payment_status='Paid').aggregate(
            total=Sum('total'))['total'] or 0
    
    def get_tier(self, obj):
        total_spent = self.get_total_spent(obj)
        if total_spent >= 30000:
            return 'Platinum'
        elif total_spent >= 10000:
            return 'Gold'
        elif total_spent >= 5000:
            return 'Silver'
        else:
            return 'Bronze'
    
    def get_is_vip(self, obj):
        return self.get_total_spent(obj) >= 30000
    
    def get_last_activity(self, obj):
        last_order = obj.orders.first()
        return last_order.created_at if last_order else obj.date_joined
    
    def get_avatar(self, obj):
        name = self.get_full_name(obj)
        return f"https://ui-avatars.com/api/?name={name}&background=random"

class CustomerCreateUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number',
            'is_active', 'role', 'password'
        ]
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class CustomerStatsOverviewSerializer(serializers.Serializer):
    total_customers = serializers.IntegerField()
    active_customers = serializers.IntegerField()
    inactive_customers = serializers.IntegerField()
    vip_customers = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    new_customers_this_month = serializers.IntegerField()