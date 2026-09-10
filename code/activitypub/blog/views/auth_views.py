from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserCreation(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
    

class SignUpView(CreateView):
    form_class = CustomUserCreation
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"