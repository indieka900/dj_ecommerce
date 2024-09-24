from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import user_logged_in
from django.contrib.auth import get_user_model

from accounts.models import CustomUser
from accounts.utils import OTPManager

User = get_user_model()

def send_registration_email(user):
    subject = 'Welcome to Our Platform'
    message = f'Hi {user.first_name},\n\nThank you for registering with us. Your account has been successfully created.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    send_mail(subject, message, from_email, recipient_list)

def send_otp_email(user : CustomUser):
    otp = OTPManager.generate_otp(user)
    subject = 'Your OTP for Login Verification'
    message = f'Hi {user.first_name},\n\nYour OTP for login verification is: {otp}\nThis OTP will expire in 10 minutes.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    print(f"{otp} ---- {user.email}")
    send_mail(subject, message, from_email, recipient_list)

@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    if created:
        send_registration_email(instance)

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    otp = OTPManager.generate_otp(user)
    # Store OTP in session or database
    request.session['login_otp'] = otp
    request.session['login_otp_timestamp'] = datetime.now().timestamp()
    send_otp_email(user, otp)