# payments/views.py
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .services import MpesaService, PaymentService
from .utils import format_phone_number
from .models import Transaction
from ecommerce.models import Order
import json

def index(request):
    return render(request, 'index.html')

@csrf_exempt
@require_http_methods(["POST"])
def initiate_payment(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        try:
            phone = format_phone_number(request.POST.get('phone'))
        except ValueError as e:
            raise ValueError(f"Invalid phone number: {str(e)}")
        
        transaction = PaymentService.create_payment_for_order(order,"mpesa", phone_number=phone)
        
        return redirect('waiting_page', transaction_id=transaction.id)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def callback(request):
    print(f"Request body: {request.body}, method: {request.method}")
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mpesa_service = MpesaService()
            success = mpesa_service.process_callback(data)
            return JsonResponse({"success": success})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)

def waiting_page(request, transaction_id):
    transaction = Transaction.objects.get(id=transaction_id)
    return render(request, 'waiting.html', {
        'transaction': transaction,
        'order': transaction.order
    })

def check_payment_status(request, transaction_id):
    transaction = Transaction.objects.get(id=transaction_id)
    return JsonResponse({
        "status": transaction.status,
        "order_id": transaction.order.id if transaction.order else None
    })
    
"""http://127.0.0.1:8000/payment/payment-success/?paymentId=PAYID-M5ZJA5I47G06661UD320535J&token=EC-46K73850Y9194081C&PayerID=FYQJBA2ECFCQJ"""


def payment_success(request):
    paymentId = request.GET.get('paymentId')
    PayerID = request.GET.get('PayerID')
    PaymentService().process_paypal_execution(paymentId, PayerID)
    return render(request, 'payment_success.html')

def payment_failed(request):
    return render(request, 'payment_failed.html')


def payment_cancelled(request):
    return render(request, 'payment_cancelled.html')