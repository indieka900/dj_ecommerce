# payments/services.py
import base64
import requests
import paypalrestsdk
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass
from .utils import convert_kes_to_usd
from django.conf import settings
from typing import Dict, Any, List
from accounts.models import CustomUser
from .models import Transaction
from ecommerce.models import Order
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

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

@dataclass
class PayPalItem:
    name: str
    sku: str
    price: str
    currency: str
    quantity: int

class PayPalService:
    @staticmethod
    def _create_product_items(order: Order) -> tuple[List[Dict[str, Any]], Decimal]:
        """Create PayPal items from order products and return total"""
        items = []
        items_total = Decimal('0.00')
        
        for order_item in order.items.all():
            item_price_usd = convert_kes_to_usd(int(order_item.unit_price))
            items.append(PayPalItem(
                name=order_item.product_name,
                sku=str(order_item.product.id),
                price=str(item_price_usd),
                currency="USD",
                quantity=order_item.quantity
            ).__dict__)
            items_total += Decimal(str(item_price_usd)) * order_item.quantity
            
        return items, items_total

    @staticmethod
    def _add_shipping_and_tax(order: Order, items: List[Dict[str, Any]], items_total: Decimal) -> tuple[List[Dict[str, Any]], Decimal]:
        """Add shipping and tax items if applicable"""
        if order.shipping_cost > 0:
            shipping_usd = convert_kes_to_usd(int(order.shipping_cost))
            items.append(PayPalItem(
                name="Shipping Cost",
                sku="SHIPPING",
                price=str(shipping_usd),
                currency="USD",
                quantity=1
            ).__dict__)
            items_total += Decimal(str(shipping_usd))
        
        if order.tax > 0:
            tax_usd = convert_kes_to_usd(int(order.tax))
            items.append(PayPalItem(
                name="Tax",
                sku="TAX",
                price=str(tax_usd),
                currency="USD",
                quantity=1
            ).__dict__)
            items_total += Decimal(str(tax_usd))
            
        return items, items_total

    @staticmethod
    def _adjust_rounding_differences(items: List[Dict[str, Any]], items_total: Decimal, total_usd: Decimal) -> None:
        """Adjust for any rounding differences between items total and order total"""
        if abs(total_usd - items_total) > Decimal('0.01'):
            difference = total_usd - items_total
            last_item = items[-1]
            original_price = Decimal(last_item["price"])
            last_item["price"] = f"{(original_price + difference):.2f}"

    @staticmethod
    def _create_shipping_address(address) -> Dict[str, str]:
        """Create PayPal shipping address dictionary"""
        return {
            "recipient_name": f"{address.first_name} {address.last_name}",
            "line1": address.street_address,
            "line2": address.apartment,
            "city": address.city,
            "state": address.county,
            "postal_code": address.postal_code,
            "country_code": "KE"
        }

    @staticmethod
    def _create_payment_data(order: Order, items: List[Dict[str, Any]], total_usd: str,
                           return_url: str, cancel_url: str) -> Dict[str, Any]:
        """Create the PayPal payment data dictionary"""
        return {
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
                    "shipping_address": PayPalService._create_shipping_address(order.shipping_address)
                },
                "amount": {
                    "total": total_usd,
                    "currency": "USD"
                },
                "description": f"Payment for Order #{order.order_number}"
            }]
        }

    @staticmethod
    def create_payment(order: Order, return_url: str, cancel_url: str) -> Dict[str, Any]:
        """Create PayPal payment for an order"""
        # Create items from products
        items, items_total = PayPalService._create_product_items(order)
        
        # Add shipping and tax items
        items, items_total = PayPalService._add_shipping_and_tax(order, items, items_total)
        
        # Convert total order amount
        total_usd = Decimal(str(convert_kes_to_usd(int(order.total))))
        
        # Adjust for any rounding differences
        PayPalService._adjust_rounding_differences(items, items_total, total_usd)
        
        # Create payment data
        payment_data = PayPalService._create_payment_data(
            order, items, str(total_usd), return_url, cancel_url
        )
        
        # Create and process payment
        payment = paypalrestsdk.Payment(payment_data)
        
        if payment.create():
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
        print(execution_response)
        if execution_response["status"] == "success":
            # Send confirmation email with PayPal receipt link
            PayPalReceiptService.send_payment_confirmation(transaction.order, payment_id)
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
    
    
class PayPalReceiptService:
    @staticmethod
    def send_payment_confirmation(order: Order, payment_id: str):
        """Send payment confirmation email with PayPal receipt link"""
        try:
            # Get payment details from PayPal
            payment = paypalrestsdk.Payment.find(payment_id)
            
            # Get the receipt URL from PayPal
            receipt_url = next(
                (link.href for link in payment.links if link.rel == "receipt"),
                None
            )
            print(receipt_url)
            
            subject = f'Payment Confirmation - Order #{order.order_number}'
            
            # Generate email content
            context = {
                'order': order,
                'payment_id': payment_id,
                'customer_name': f"{order.shipping_address.first_name} {order.shipping_address.last_name}",
                'receipt_url': receipt_url
            }
            
            html_content = render_to_string('emails/paypal_confirmation.html', context)
            
            # Create and send email
            
            email = EmailMultiAlternatives(
                    subject,
                    body=html_content,
                    to=[order.user.email]
                )
            email.attach_alternative(html_content, "text/html")
            
            email.send()
            
            return True
        except Exception as e:
            print(f"Error sending payment confirmation: {str(e)}")
            return False
