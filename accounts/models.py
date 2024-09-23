from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.contrib.auth.validators import UnicodeUsernameValidator
from django_otp.oath import TOTP
from django_otp.util import random_hex

class UserAdress(models.Model):
    _id = models.CharField(primary_key=True, editable=False,max_length=255)
    address_line = models.CharField( max_length=100)
    city = models.CharField( max_length=70)
    post_code = models.IntegerField()
    state = models.CharField( max_length=70)
    district = models.CharField( max_length=100)
    county = models.CharField( max_length=60)
    default = models.BooleanField(default=False)
    deliveryInstructions = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.city} --- {self.county}"

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", 'Administrator')
        return self.create_user(email, password, **extra_fields)
class CustomUser(AbstractBaseUser, PermissionsMixin):
    Role_choices = (
        ("Administrator", "Administrator"),
        ("Customer", "Customer"),
    )
    
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    phone_number = models.CharField(max_length=15, default='')
    role = models.CharField(max_length=25, choices=Role_choices, default="Customer")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    secret = models.CharField(max_length=255, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def save(self, *args, **kwargs):
        if not self.secret:
            self.secret = random_hex(20)
        super().save(*args, **kwargs)

    '''def generate_totp_token(self):
        totp = TOTP(key=self.otp_secret, digits=6)  # Adjust interval to match the one used in OTPManager
        return totp.token()'''

    
    '''def verify_totp_token(self, token):
        totp = TOTP(key=self.otp_secret, digits=6)  # Adjust interval to match the one used in OTPManager
        return totp.verify(token)'''


class Profile(models.Model):
    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE, unique=True,related_name='%(class)s_profile')
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    street_address = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profile",default="default.png")
    
    class Meta:
        abstract= True