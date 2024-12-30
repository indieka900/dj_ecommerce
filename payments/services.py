# payments/services.py
import base64
from datetime import datetime
from decimal import Decimal
import requests
from .utils import convert_kes_to_usd
from django.conf import settings
import paypalrestsdk
from typing import Dict, Any
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

        
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_ID,
    "client_secret": settings.PAYPAL_SECRET
})

class PayPalService:
    @staticmethod
    def create_payment(order: Order, return_url: str, cancel_url: str) -> Dict[str, Any]:
        """Create PayPal payment for an order"""
        items = []
        for order_item in order.items.all():  # Fetch related OrderItem objects
            items.append({
                "name": order_item.product_name,
                "sku": str(order_item.product.id),
                "price": convert_kes_to_usd(int(order_item.unit_price)),  # Ensure price is a string
                "currency": "USD",
                "quantity": order_item.quantity
            })
        '''if order.shipping_cost > 0:
            items.append({
                "name": "Shipping Cost",
                "sku": "SHIPPING",
                "price": convert_kes_to_usd(int(order.shipping_cost)),
                "currency": "USD",
                "quantity": 1
            })
        
        if order.tax > 0:
            items.append({
                "name": "Tax",
                "sku": "TAX",
                "price": convert_kes_to_usd(int(order.tax)),
                "currency": "USD",
                "quantity": 1
            })'''
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": return_url,
                "cancel_url": cancel_url
            },
            "transactions": [{
                "item_list": {
                    "items": items,
                    "shipping_address": {
                        "recipient_name": f"{order.shipping_address.first_name} {order.shipping_address.last_name}",
                        "line1": order.shipping_address.street_address,
                        "line2": order.shipping_address.apartment,
                        "city": order.shipping_address.city,
                        "state": order.shipping_address.county,
                        "postal_code": order.shipping_address.postal_code,
                        "country_code": "KE"
                    }
                },
                "amount": {
                    "total": convert_kes_to_usd(int(order.total)),
                    "currency": "USD"
                },
                "description": f"Payment for Order #{order.order_number}"
            }]
        })

        if payment.create():
            print(payment)
            return {
                "status": "success",
                "payment_id": payment.id,
                "approval_url": next(link.href for link in payment.links if link.rel == "approval_url")
            }
        else:
            return {
                "status": "error",
                "message": payment.error
            }

    @staticmethod
    def execute_payment(payment_id: str, payer_id: str) -> Dict[str, Any]:
        """Execute a previously created PayPal payment"""
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            return {
                "status": "success",
                "transaction_id": payment.transactions[0].related_resources[0].sale.id
            }
        else:
            return {
                "status": "error",
                "message": payment.error
            }

class PaymentService:
    def __init__(self):
        self.mpesa_service = MpesaService()
        self.paypal_service = PayPalService()

    def create_payment_for_order(self, order: Order, payment_method: str, **kwargs) -> Transaction:
        """Create a payment transaction for an order"""
        user = CustomUser.objects.get(id=4)  # You might want to modify this to get the actual user
        phone_number = kwargs.get('phone_number')
        # Create initial transaction record
        transaction = Transaction.objects.create(
            user=user,
            order=order,
            amount=int(order.total),
            status="Pending",
            phone_number = phone_number,
            payment_method=payment_method
        )

        if payment_method == "mpesa":
            phone_number = kwargs.get('phone_number')
            if not phone_number:
                raise ValueError("Phone number is required for M-PESA payments")
            
            stk_response = self.mpesa_service.initiate_stk_push(
                phone=phone_number,
                amount=int(order.total),
                order_id=order.order_number
            )
            transaction.transaction_id = stk_response.get('CheckoutRequestID')
            
        elif payment_method == "paypal":
            return_url = kwargs.get('return_url')
            cancel_url = kwargs.get('cancel_url')
            if not (return_url and cancel_url):
                raise ValueError("Return and cancel URLs are required for PayPal payments")
            
            paypal_response = self.paypal_service.create_payment(
                order=order,
                return_url=return_url,
                cancel_url=cancel_url
            )
            print(paypal_response)
            
            if paypal_response["status"] == "success":
                transaction.transaction_id = paypal_response["payment_id"]
                transaction.payment_url = paypal_response["approval_url"]
            else:
                transaction.status = "Failed"
                transaction.notes = paypal_response.get("message", "PayPal payment creation failed")
        
        else:
            raise ValueError(f"Unsupported payment method: {payment_method}")
        
        transaction.save()
        return transaction

    def process_paypal_execution(self, payment_id: str, payer_id: str) -> bool:
        """Process PayPal payment execution"""
        transaction = Transaction.objects.filter(
            transaction_id=payment_id,
            payment_method="paypal"
        ).first()
        
        if not transaction:
            return False

        execution_response = self.paypal_service.execute_payment(payment_id, payer_id)
        
        if execution_response["status"] == "success":
            transaction.status = "Success"
            transaction.transaction_date = datetime.now()
            transaction.receipt_number = execution_response["transaction_id"]
            transaction.save()

            # Update order status
            order = transaction.order
            order.payment_status = "Paid"
            order.save()
            
            return True
        else:
            transaction.status = "Failed"
            transaction.notes = execution_response.get("message", "PayPal payment execution failed")
            transaction.save()
            return False
    