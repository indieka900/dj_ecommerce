from django import forms

class CheckoutForm(forms.Form):
    # Billing Address Fields
    billing_first_name = forms.CharField(max_length=255)
    billing_last_name = forms.CharField(max_length=255)
    billing_email = forms.EmailField()
    billing_phone = forms.CharField(max_length=20)
    billing_street_address = forms.CharField(max_length=255)
    billing_apartment = forms.CharField(max_length=255, required=False)
    billing_city = forms.CharField(max_length=100)
    billing_county = forms.CharField(max_length=100)
    # billing_country = forms.CharField(max_length=100)
    billing_postal_code = forms.CharField(max_length=20)
    
    # Shipping Address Fields
    shipping_first_name = forms.CharField(max_length=255, required=False)
    shipping_last_name = forms.CharField(max_length=255, required=False)
    shipping_email = forms.EmailField(required=False)
    shipping_phone = forms.CharField(max_length=20, required=False)
    shipping_street_address = forms.CharField(max_length=255, required=False)
    shipping_apartment = forms.CharField(max_length=255, required=False)
    shipping_city = forms.CharField(max_length=100, required=False)
    shipping_county = forms.CharField(max_length=100, required=False)
    # shipping_country = forms.CharField(max_length=100, required=False)
    shipping_postal_code = forms.CharField(max_length=20, required=False)
    
    # Checkbox for same as billing
    different_shipping_loc = forms.CharField(max_length=20, required=False)
    
    # Order notes
    order_notes = forms.CharField(widget=forms.Textarea, required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'text-field'})

    def clean(self):
        cleaned_data = super().clean()
        different_shipping_loc = cleaned_data.get('different_shipping_loc')
        print(different_shipping_loc)
        
        if different_shipping_loc:
            # If shipping is different, validate shipping address fields
            shipping_fields = ['shipping_first_name','shipping_last_name', 
                             'shipping_street_address', 'shipping_city', 
                             'shipping_county', 'shipping_postal_code',
                             'shipping_email', 'shipping_phone', 'shipping_apartment']
            
            for field in shipping_fields:
                # print(field)
                if not cleaned_data.get(field):
                    if field == 'shipping_apartment':
                        continue
                    self.add_error(field, 'This field is required when shipping address is different.')
        return cleaned_data
