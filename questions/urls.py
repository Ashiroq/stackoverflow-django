from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'questions'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^search/$', views.SearchView.as_view(), name='search'),
    url(r'^questions/(?P<pk>[0-9]+)/$', views.QuestionView.as_view(), name='question'),
    url(r'^questions/ask/$', views.AskView.as_view(), name='ask'),
    url(r'^questions/(?P<pk>[0-9]+)/answer/$', views.AddAnswer.as_view(), name='answer'),
    url(r'^questions/(?P<q_pk>[0-9]+)/(?P<pk>[0-9]+)/delete/$', views.AnswerDeleteView.as_view(), name='answer_delete'),
    url(r'^questions/(?P<q_pk>[0-9]+)/(?P<pk>[0-9]+)/edit/$', views.AnswerEditView.as_view(), name='answer_edit'),
    url(r'^questions/(?P<q_pk>[0-9]+)/(?P<pk>[0-9]+)/accept/$', views.accept_answer, name='answer_accept'),
    url(r'^questions/(?P<pk>[0-9]+)/delete/$', views.QuestionDeleteView.as_view(), name='question_delete'),
    url(r'^questions/(?P<pk>[0-9]+)/edit/$', views.QuestionEditView.as_view(), name='question_edit'),
    url(r'^questions/tagged/(?P<tag>[\w\s\(\)]+)/$', views.TaggedView.as_view(), name='tagged'),
    url(r'^users/(?P<pk>[0-9]+)/$', views.UserView.as_view(), name='user'),
    url(r'^users/(?P<pk>[0-9]+)/edit/$', views.UserEditView.as_view(), name='user_edit'),
    # url(r'^users/(?P<pk>[0-9]+)/settings/$', views.account_settings, name='user_settings'),
    url(r'^users/(?P<pk>[0-9]+)/settings/$', views.AccountSettings.as_view(), name='user_settings'),
    url(r'^register/$', views.register, name='register')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
