from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField

class CustomAuthForm(AuthenticationForm):
    username = UsernameField(
        max_length=254,
        widget=forms.TextInput(attrs={'autofocus': True, 'value': 'guest'})
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'value': 'Gu3s$tTq'})
    )
