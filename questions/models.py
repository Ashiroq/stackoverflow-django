from django.db import models
from django.dispatch import receiver
from django.forms import TextInput
from django_resized import ResizedImageField
from django.utils.deconstruct import deconstructible
from django.contrib.auth.models import User as AuthUser
from django.db.models.signals import post_save, post_delete
from django.contrib.postgres.fields import ArrayField
from django.core.files.storage import default_storage

# Create your models here.

@deconstructible
class Rename(object):
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        name = "%s.%s" % (instance.user.pk, ext)
        return self.path + name

class UserProfile(models.Model):
    user = models.OneToOneField(AuthUser)
    avatar = ResizedImageField(size=[128, 128], crop=['middle', 'center'], upload_to=Rename('avatars/'), default='avatars/default.png')
    description = models.TextField(null=True)
    location = models.CharField(max_length=100, null=True)
    links = ArrayField(models.CharField(max_length=100), size=10, null=True)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        try:
            current = UserProfile.objects.get(id=self.id)
            if current.avatar != current.avatar.field.default and current.avatar != self.avatar:
                current.avatar.delete(save=False)
        except: pass
        super(UserProfile, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return '/users/%i' % self.user.id

@receiver(post_save, sender=AuthUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=AuthUser)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

@receiver(post_delete, sender=UserProfile)
def delete_avatar_file(sender, instance, **kwargs):
    if instance.avatar.name != 'avatars/default.png':
        default_storage.delete(instance.avatar.name)

class Tag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Question(models.Model):
    title = models.CharField(max_length=200, null=False)
    text = models.TextField(null=False, editable=True)
    creation_time = models.DateTimeField()
    owner = models.ForeignKey(AuthUser)
    tags = models.ManyToManyField(Tag, blank=True)

    def get_absolute_url(self):
        return '/questions/%i/' % self.id

    def __str__(self):
        return self.title

class Answer(models.Model):
    text = models.TextField(null=False)
    creation_time = models.DateTimeField()
    owner = models.ForeignKey(AuthUser)
    question = models.ForeignKey(Question)
    is_accepted = models.BooleanField(null=False, default=False)

    def get_absolute_url(self):
        return '/questions/%i/' % self.question.id

    def __str__(self):
        return self.question.title + ', ' + self.owner.username
