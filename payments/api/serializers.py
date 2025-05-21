from payments.models import Transaction
from rest_framework import serializers

class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.email')
    order = serializers.ReadOnlyField(source='order.order_number')
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('id', 'timestamp', 'transaction_id', 'amount', 'payment_url')