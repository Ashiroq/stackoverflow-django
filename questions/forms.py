from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ClearableFileInput
from django.contrib.auth.models import User

from .models import Answer, UserProfile, Question

class CustomClearableFileInput(ClearableFileInput):
    template_name = 'custom_clearable_file_input.html'


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text']

class RegisterForm(UserCreationForm):
    
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True

    class Meta:
        model = User
        fields = ('username', 'email')


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('avatar', 'description', 'location', 'links')
        widgets = {
            'avatar': CustomClearableFileInput
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name')

class EmailChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']

    def __init__(self, *args, **kwargs):
        # if instance is None:
        #     raise ValueError
        super(EmailChangeForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(EmailChangeForm, self).clean()
        if cleaned_data['email'] == self.instance.email:
            self.add_error('email', 'This is your current email.')
        return cleaned_data
