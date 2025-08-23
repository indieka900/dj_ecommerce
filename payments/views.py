# payments/views.py
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.urls import reverse
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
    print(f"Request body: {request.body}")
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
    

@csrf_exempt
def payment_status(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        print("Callback received:", data)
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
    return JsonResponse({"error": "Invalid method"}, status=405)

def payment_success(request):
    paymentId = request.GET.get('paymentId')
    PayerID = request.GET.get('PayerID')
    if paymentId and PayerID:
        PaymentService().process_paypal_execution(paymentId, PayerID)
    return render(request, 'payment_success.html')

def payment_failed(request):
    return render(request, 'payment_failed.html')


def payment_cancelled(request):
    return render(request, 'payment_cancelled.html')