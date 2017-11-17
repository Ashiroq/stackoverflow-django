from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ClearableFileInput
from django.contrib.auth.models import User

from .models import Answer, UserProfile, Question, Tag

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

class QuestionAskForm(forms.ModelForm):
    tags = forms.CharField()
    class Meta:
        model = Question
        fields = ('title', 'text')
    
    def __init__(self, *args, **kwargs):
        super(QuestionAskForm, self).__init__(*args, **kwargs)
        self.fields['tags'].required = False

    def clean_tags(self):
        """
            Tags string to array with whitespace verification
        """
        tags_string = self.cleaned_data['tags'].strip()
        if tags_string == '':
            self.tags = None
            return

        tags_array = tags_string.split(',')

        # Removes whitespaces for all tag
        tags = [t.strip() for t in tags_array]
        self.tags = []
        for t in tags:
            if t == '':
                continue

            # Checks if tag exists and creates it if not
            try:
                filtered = Tag.objects.get(name__exact=t)
                self.tags.append(filtered)
            except Tag.DoesNotExist:
                self.tags.append(Tag.objects.create(name=t))

    def save(self, commit=True):
        question = super(QuestionAskForm, self).save(commit=commit)
        if self.tags is not None:
            for t in self.tags:
                question.tags.add(t)
        return question

class QuestionEditForm(QuestionAskForm):
    def __init__(self, *args, **kwargs):
        super(QuestionEditForm, self).__init__(*args, **kwargs)
        # Tags queryset to string as CharField initial value
        tags_array = [t.name for t in kwargs['instance'].tags.all()]
        self.fields['tags'].initial = ', '.join(tags_array)

    def save(self, commit=True):
        question = super(QuestionEditForm, self).save(commit=commit)
        question.tags.clear()
        if self.tags is not None:
            for t in self.tags:
                question.tags.add(t)
        return question

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
