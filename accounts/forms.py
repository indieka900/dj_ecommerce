from django import forms
from accounts.models import CustomUser, ContactUs, Address

class UserSignUpForm(forms.ModelForm):
    email = forms.EmailField(max_length=156, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
    class Meta:
        model = CustomUser
        fields = ("email","phone_number","first_name")

    password1 = forms.CharField(
        label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Password Confirmation",
        widget=forms.PasswordInput)


    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match!")

        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        # user.is_active = False
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()

        return user
    
    
class ContactForm(forms.ModelForm):
    
    class Meta:
        model = ContactUs
        fields = ['full_name', 'email', 'subject', 'message']
        
class AddressForm(forms.ModelForm):
    
    class Meta:
        model = Address
        fields = ('email', 'first_name', 'last_name', 'phone', 'street_address', 'apartment', 'city', 'county', 'postal_code', 'is_default', 'notes')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required
        for field in self.fields:
            self.fields[field].required = True
        # Apartment is optional
        self.fields['apartment'].required = False
        self.fields['notes'].required = False