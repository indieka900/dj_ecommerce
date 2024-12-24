# payments/services.py
import base64
from datetime import datetime
import requests
from django.conf import settings

from accounts.models import CustomUser
from .models import Transaction
from ecommerce.models import Order

class MpesaService:
    def __init__(self):
        self.base_url = settings.BASE_URL
        self.consumer_key = settings.CONSUMER_KEY
        self.consumer_secret = settings.CONSUMER_SECRET
        self.shortcode = settings.SHORTCODE
        self.passkey = settings.PASSKEY

    def generate_access_token(self):
        auth_url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
        response = requests.get(auth_url, auth=(self.consumer_key, self.consumer_secret))
        return response.json().get('access_token')

    def generate_password(self):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = f'{self.shortcode}{self.passkey}{timestamp}'
        return base64.b64encode(data_to_encode.encode()).decode(), timestamp

    def initiate_stk_push(self, phone, amount, order_id):
        """Initiate STK push and create transaction record"""
        access_token = self.generate_access_token()
        password, timestamp = self.generate_password()

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": self.shortcode,
            "PhoneNumber": phone,
            "CallBackURL": "https://95b2-197-237-67-23.ngrok-free.app/payment/callback/",
            "AccountReference": f"Order_{order_id}",
            "TransactionDesc": "Payment for order"
        }

        response = requests.post(
            f'{self.base_url}/mpesa/stkpush/v1/processrequest',
            json=payload,
            headers=headers
        )
        return response.json()

    def process_callback(self, callback_data):
        """Process the callback data from Mpesa"""
        stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        
        transaction = Transaction.objects.filter(transaction_id=checkout_request_id).first()
        if not transaction:
            return False

        if result_code == 0:
            # Payment successful
            callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            receipt_number = next((item['Value'] for item in callback_metadata if item['Name'] == 'MpesaReceiptNumber'), None)
            
            transaction.status = "Success"
            transaction.receipt_number = receipt_number
            transaction.save()

            # Update order status
            order = Order.objects.filter(id=transaction.order.id).first()
            if order:
                order.payment_status = "Paid"
                order.save()

            return True
        else:
            transaction.status = "Failed"
            transaction.save()
            return False

class PaymentService:
    @staticmethod
    def create_payment_for_order(order:Order, phone_number):
        """Create a payment transaction for an order"""
        mpesa = MpesaService()
        user = CustomUser.objects.get(id=4)
        
        # Create transaction record
        transaction = Transaction.objects.create(
            user = user,
            order=order,
            phone_number=phone_number,
            amount=int(order.total),
            status="Pending"
        )

        # Initiate payment
        stk_response = mpesa.initiate_stk_push(
            phone=phone_number,
            amount=int(order.total),
            order_id=order.order_number
        )

        # Update transaction with Mpesa response
        transaction.transaction_id = stk_response.get('CheckoutRequestID')
        transaction.save()

        return transaction
    
def format_phone_number(phone_number):
    """
    Format phone number to start with 254 and be 12 digits long.
    Examples:
        0712345678 -> 254712345678
        +254712345678 -> 254712345678
        712345678 -> 254712345678
    """
    # Remove any spaces, hyphens or plus signs
    phone = phone_number.strip().replace(' ', '').replace('-', '').replace('+', '')
    
    # If number starts with 0, remove it
    if phone.startswith('0'):
        phone = phone[1:]
    
    # If number starts with 254, use it as is
    if phone.startswith('254'):
        phone = phone
    # Otherwise, add 254 prefix
    else:
        phone = f"254{phone}"
    
    # Verify the length
    if len(phone) != 12:
        raise ValueError("Phone number must be 9 digits after the prefix")
        
    return phone