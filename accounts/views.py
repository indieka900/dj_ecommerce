from django.shortcuts import render, redirect
from .models import CustomUser
from django.views.generic import CreateView
from accounts.forms import UserSignUpForm
from django.contrib.auth import login, authenticate
from django.contrib import messages


class SignupView(CreateView):
    model = CustomUser
    form_class = UserSignUpForm
    template_name = "account.html"

    def form_valid(self, form):
        if form.is_valid():
            print(self.request.POST)
            user = form.save(commit=False)
            # user.role = self.request.POST.get('user_type')
            print(user)
            user.save()
            return redirect('/')
            
        return render(self.request, "account.html")
    
    
def login_user(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user= CustomUser.objects.get(email=email)
            # user.set_password(password)
        except CustomUser.DoesNotExist:
            messages.error(request, 'email does not exist!') 
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, 'Logged in succesfully')
                return redirect('/')
            else:
                messages.error(request, 'Please activate your account')
                return redirect('/') 
        else:
            messages.error(request, 'Incorrect password')
            return redirect('/')
        
def error_404_view(request, exception):
   
    return render(request, '404.html')