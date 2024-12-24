from django.db import models
from django.conf import settings
from ecommerce.models import Order

class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    receipt_number = models.CharField(max_length=50, blank=True, null=True) 
    status = models.CharField(max_length=50, blank=True, null=True)
    transaction_id = models.CharField(max_length=120, null=True) # 'ch_1H7b8z2eZvKYlo2CwZ3J9J1N'
    description = models.TextField(blank=True, null=True)  
    transaction_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Transaction {self.receipt_number or self.transaction_id} - {self.status}"