from django.shortcuts import render, redirect, reverse, Http404, get_object_or_404
from django.conf import settings
from django.utils import timezone
from django.views import generic
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.postgres.search import SearchVector, SearchQuery

from .multiform import MultiFormsView
from .models import Question, UserProfile, Answer
from .forms import AnswerForm, RegisterForm, ProfileUpdateForm, UserUpdateForm, EmailChangeForm, QuestionEditForm, QuestionAskForm

# Create your views here.
class IndexView(generic.ListView):
    template_name = 'questions/index.html'
    context_object_name = 'questions'

    def get_queryset(self):
        return Question.objects.order_by('-creation_time')

class QuestionView(generic.DetailView):
    template_name = 'questions/question.html'
    model = Question

    def get_queryset(self):
        return Question.objects.filter(pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super(QuestionView, self).get_context_data(**kwargs)
        context['question'] = Question.objects.get(pk=self.kwargs['pk'])
        context['answers'] = list(Answer.objects.filter(question=self.kwargs['pk'], is_accepted=True)) + \
                            list(Answer.objects.filter(question=self.kwargs['pk'], is_accepted=False).order_by('-creation_time'))
        context['form'] = AnswerForm
        return context

class UserView(generic.DetailView):
    template_name = 'questions/user.html'
    context_object_name = 'profile'
    model = User

    def get_queryset(self):
        return User.objects.filter(pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super(UserView, self).get_context_data(**kwargs)
        context['form'] = ProfileUpdateForm
        user = User.objects.get(pk=self.kwargs['pk'])
        context['created_questions'] = Question.objects.filter(owner=user).order_by('-creation_time')[:5]
        context['posted_answers'] = Answer.objects.filter(owner=user).order_by('-creation_time')[:5]
        return context

class UserEditView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = UserProfile
    template_name_suffix = '_edit'
    login_url = '/'
    redirect_field_name = None
    form_class = ProfileUpdateForm

    # https://stackoverflow.com/questions/15497693/django-can-class-based-views-accept-two-forms-at-a-time/15499249#15499249
    second_form_class = UserUpdateForm

    def get_context_data(self, **kwargs):
        context = super(UserEditView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        if 'form' not in context:
            context['form'] = self.form_class(request=self.request)
        if 'form2' not in context:
            initial = {
                'username': context['user'].username,
                'first_name': context['user'].first_name,
                'last_name': context['user'].last_name
            }
            context['form2'] = self.second_form_class(initial=initial)
        return context

    def form_invalid(self, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))

    def test_func(self):
        return self.request.user == User.objects.get(pk=self.kwargs['pk'])

    def get_form(self, form_class=None):
        form = super(UserEditView, self).get_form(form_class)
        form.fields['description'].required = False
        form.fields['location'].required = False
        form.fields['links'].required = False
        return form

    def get_second_form(self, second_form_class=None):
        return super(UserEditView, self).get_form(second_form_class)

    def get_success_url(self):
        return '/users/%i' % self.request.user.id

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        form = self.get_form(self.form_class)
        form2 = self.get_second_form(self.second_form_class)
        form2.instance = self.object.user

        fields = [f for f in form.fields]
        fields += [f for f in form2.fields]

        if form2.is_valid():
            self.form_valid(form2)
        else:
            return self.form_invalid(**{'form2': form2})

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(**{'form': form})

def account_settings(request, **kwargs):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('questions:user', user.id)
        else:
            messages.error(request, 'Something went wrong.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'questions/user_settings.html', {'form': form})

class AccountSettings(LoginRequiredMixin, UserPassesTestMixin, MultiFormsView):
    template_name = 'questions/user_settings.html'
    form_classes = {
        'change_password': PasswordChangeForm,
        'change_email': EmailChangeForm
    }

    def test_func(self):
        return self.request.user == User.objects.get(pk=self.kwargs['pk'])

    def get_change_email_initial(self):
        return {'email': self.request.user.email}

    def create_change_password_form(self, **kwargs):
        return PasswordChangeForm(self.request.user, **kwargs)

    def create_change_email_form(self, **kwargs):
        return EmailChangeForm(instance=self.request.user, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AccountSettings, self).get_context_data(**kwargs)
        return context

    def change_email_form_valid(self, form):
        print(form.__dict__)
        messages.success(self.request, "Email changed")
        user = form.save()
        print(user.email)
        print(settings.EMAIL_HOST_USER)
        ''' 
        To enable sending emails, uncoment email settings in settings.py and fill in credentials in email_credentials.py.
        Using smtp.gmail.com requires turning on less secure apps: https://www.google.com/settings/security/lesssecureapps

        send_mail('Subject', 'Message', settings.EMAIL_HOST_USER, [user.email])
        '''
        return redirect('questions:user_settings', self.request.user.id)

    def change_password_form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, "Password changed.")
        return redirect('questions:user_settings', user.id)

def register(request):
    form = RegisterForm(request.POST)
    if form.is_valid():
        form.save()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(request, user)
        return redirect(reverse('questions:index'))
    return render(request, 'questions/register.html', {'register_form': form})

class AddAnswer(LoginRequiredMixin, generic.CreateView):
    model = Answer
    fields = ['text']
    login_url = '/login'
    redirect_field_name = None

    def get(self, request, *args, **kwargs):
        raise Http404

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.creation_time = timezone.now()
        form.instance.question = Question.objects.get(pk=self.kwargs['pk'])
        return super(AddAnswer, self).form_valid(form)

class AskView(LoginRequiredMixin, generic.CreateView):
    model = Question
    # fields = ['title', 'text', 'tags']
    template_name = 'questions/ask.html'
    login_url = '/login'
    redirect_field_name = None
    form_class = QuestionAskForm

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.creation_time = timezone.now()
        return super(AskView, self).form_valid(form)

class QuestionDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = Question
    success_url = '/'
    login_url = '/'
    redirect_field_name = None

    def test_func(self):
        return self.request.user == Question.objects.get(pk=self.kwargs['pk']).owner

class QuestionEditView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    # model = Question
    # fields = ['title', 'text', 'tags']
    form_class = QuestionEditForm
    template_name_suffix = '_edit'
    login_url = '/'
    redirect_field_name = 'title'

    def get_queryset(self):
        return Question.objects.filter(pk=self.kwargs['pk'])

    def test_func(self):
        return self.request.user == Question.objects.get(pk=self.kwargs['pk']).owner

class AnswerDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = Answer
    success_url = ''
    login_url = '/'
    redirect_field_name = None

    def get_success_url(self):
        return reverse('questions:question', args=(self.object.question.id,))

    def test_func(self):
        return self.request.user == Answer.objects.get(pk=self.kwargs['pk']).owner

class AnswerEditView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = Answer
    fields = ['text']
    template_name_suffix = '_edit'
    login_url = '/'
    redirect_field_name = None

    def test_func(self):
        return self.request.user == Answer.objects.get(pk=self.kwargs['pk']).owner

@login_required
def accept_answer(request, *args, **kwargs):
    # Requires fetch/ajax in template
    # if not request.method == "POST":
    #     raise Http404
    question = Question.objects.get(pk=kwargs['q_pk'])
    if request.user == question.owner:
        answers = Answer.objects.filter(question=question)
        for answer in answers:
            answer.is_accepted = answer.id == int(kwargs['pk'])
            answer.save()
    return redirect(reverse('questions:question', args=(kwargs['q_pk'],)))

class SearchView(generic.ListView):
    model = Question
    template_name = 'questions/search.html'
    context_object_name = 'questions'

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context['query'] = self.request.GET['q']
        return context

    def get_queryset(self):
        return Question.objects.annotate(
            search=SearchVector('title', 'text')
        ).filter(search=SearchQuery(self.request.GET['q']))

class TaggedView(generic.ListView):
    model = Question
    template_name = 'questions/tagged.html'
    context_object_name = 'questions'

    def get_context_data(self, **kwargs):
        context = super(TaggedView, self).get_context_data(**kwargs)
        context['tag'] = self.kwargs['tag']
        return context

    def get_queryset(self):
        return Question.objects.filter(tags__name=self.kwargs['tag'])
