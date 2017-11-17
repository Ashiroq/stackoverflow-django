from django.test import TestCase
from django.shortcuts import reverse, Http404
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.core.files.uploadedfile import SimpleUploadedFile
from django_resized.forms import ResizedImageFieldFile

from .models import Question, Answer, Tag

# Create your tests here.
class IndexViewTests(TestCase):

    def setUp(self):
        User.objects.create_user(username='test', password='T3Ss$tTx')

    def test_context_without_questions(self):
        result = self.client.get(reverse('questions:index'))
        self.assertEqual(result.status_code, 200)
        self.assertQuerysetEqual(result.context['questions'], [])

    def test_context_with_questions(self):
        user = User.objects.get(username__exact="test")
        question_list = []
        for _ in range(0, 10):
            q = Question.objects.create(title="Lorem ipsum?", text="Lorem ipsum.", creation_time=timezone.now(), owner=user)
            question_list.append(q)
        response = self.client.get(reverse('questions:index'))
        self.assertQuerysetEqual(response.context['questions'], ['<Question: Lorem ipsum?>' for i in range(0, 10)])

    def test_context_without_questions_logged(self):
        self.client.login(username='test', password='T3Ss$tTx')
        response = self.client.get(reverse('questions:index'))
        self.assertQuerysetEqual(response.context['questions'], [])

    def test_context_with_questions_logged(self):
        self.client.login(username='test', password='T3Ss$tTx')
        user = User.objects.get(username__exact="test")
        question_list = []
        for _ in range(0, 10):
            q = Question.objects.create(title="Lorem ipsum?", text="Lorem ipsum.", creation_time=timezone.now(), owner=user)
            question_list.append(q)
        response = self.client.get(reverse('questions:index'))
        self.assertQuerysetEqual(response.context['questions'], ['<Question: Lorem ipsum?>' for i in range(0, 10)])

def _create_answer(text, question, owner):
    return Answer.objects.create(text=text, owner=owner, creation_time=timezone.now(), question=question)

class QuestionViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='T3Ss$tTx')
        self.user2 = User.objects.create_user(username='test2', password='T3Ss$tTx')
        self.question = Question.objects.create(title="Lorem ipsum?", text="Lorem ipsum.", creation_time=timezone.now(), owner=self.user)
        self.url = reverse('questions:question', args=(self.question.id,))

    def test_context_without_answers(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['question'], self.question)
        self.assertQuerysetEqual(response.context['answers'], [])

    def test_context_with_answers(self):
        for i in range(0, 10):
            _create_answer(str(i), self.question, self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context['question'], self.question)
        self.assertQuerysetEqual(response.context['answers'], ['<Answer: Lorem ipsum?, test>' for i in range(0, 10)], ordered=False)

    def test_context_without_answers_logged(self):
        self.client.login(username='test', password='T3Ss$tTx')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['question'], self.question)
        self.assertQuerysetEqual(response.context['answers'], [])

    def test_context_with_answers_logged(self):
        self.client.login(username='test', password='T3Ss$tTx')
        for i in range(0, 10):
            _create_answer(str(i), self.question, self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context['question'], self.question)
        self.assertQuerysetEqual(response.context['answers'], ['<Answer: Lorem ipsum?, test>' for i in range(0, 10)], ordered=False)

    def test_can_accept_answer_as_owner(self):
        self.client.login(username='test', password='T3Ss$tTx')
        answer = _create_answer("testtest", self.question, self.user2)
        url = reverse('questions:answer_accept', args=(self.question.id, answer.id))
        response = self.client.post(url, {})
        self.assertIs(Answer.objects.get(pk=answer.id).is_accepted, True)

    def test_cannot_accept_answer_as_not_owner(self):
        self.client.login(username='test2', password='T3Ss$tTx')
        answer = _create_answer("testtest", self.question, self.user2)
        url = reverse('questions:answer_accept', args=(self.question.id, answer.id))
        response = self.client.post(url, {})
        self.assertIs(Answer.objects.get(pk=answer.id).is_accepted, False)

    def test_cannot_accept_answer_as_not_logged(self):
        answer = _create_answer("testtest", self.question, self.user2)
        url = reverse('questions:answer_accept', args=(self.question.id, answer.id))
        response = self.client.post(url, {})
        self.assertIs(Answer.objects.get(pk=answer.id).is_accepted, False)

class QuestionEditViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='T3Ss$tTx')
        self.user2 = User.objects.create_user(username='test2', password='T3Ss$tTx')
        self.question = Question.objects.create(title="Lorem ipsum?", text="Lorem ipsum.", creation_time=timezone.now(), owner=self.user)

    def test_can_access_edit_question_as_owner(self):
        """
         Checks if question owner can access edit page """
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:question_edit', args=(self.question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_cannot_access_edit_question_not_owner(self):
        """
         Checks if regular user can't access someone's question edit page 
        """
        self.client.login(username='test2', password='T3Ss$tTx')
        url = reverse('questions:question_edit', args=(self.question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_can_edit_question_as_owner(self):
        """
         Tests if question owner can actually update question 
        """
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:question_edit', args=(self.question.id,))
        response = self.client.post(url, {'title': 'testtesttest', 'text': 'TesT', 'tags': ''})
        updated = Question.objects.get(pk=self.question.id)
        self.assertEqual(updated.title, 'testtesttest')
        self.assertEqual(updated.text, 'TesT')
    
    def test_can_add_tags(self):
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:question_edit', args=(self.question.id,))
        tag1 = Tag.objects.create(name='test')
        tag2 = Tag.objects.create(name='lorem ipsum')
        response = self.client.post(url, {'title': 'Lorem ipsum?', 'text': 'Lorem ipsum.', 'tags': 'test, lorem ipsum'})
        updated = Question.objects.get(pk=self.question.id)
        self.assertQuerysetEqual(updated.tags.all(), ["<Tag: test>", "<Tag: lorem ipsum>"], ordered=False)

    def test_can_edit_tags(self):
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:question_edit', args=(self.question.id,))
        self.question.tags.create(name='test')
        self.question.tags.create(name='lorem ipsum')
        tag3 = Tag.objects.create(name='newtag')
        response = self.client.post(url, {'title': 'Lorem ipsum?', 'text': 'Lorem ipsum.', 'tags': 'newtag'})
        updated = Question.objects.get(pk=self.question.id)
        self.assertQuerysetEqual(updated.tags.all(), ["<Tag: newtag>"], ordered=False)

    def test_can_remove_tags(self):
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:question_edit', args=(self.question.id,))
        self.question.tags.create(name='test')
        self.question.tags.create(name='lorem ipsum')
        response = self.client.post(url, {'title': 'Lorem ipsum?', 'text': 'Lorem ipsum.', 'tags': ''})
        updated = Question.objects.get(pk=self.question.id)
        self.assertQuerysetEqual(updated.tags.all(), [], ordered=False)

    def test_cannot_edit_question_not_owner(self):
        """
         Tests if regular user cannot update question 
        """
        self.client.login(username='test2', password='T3Ss$tTx')
        url = reverse('questions:question_edit', args=(self.question.id,))
        response = self.client.post(url, {'title': 'testtesttest', 'text': 'TesT'})
        notupdated = Question.objects.get(pk=self.question.id)
        self.assertEqual(notupdated.title, self.question.title)
        self.assertEqual(notupdated.text, self.question.text)

class QuestionDeleteViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='T3Ss$tTx')
        self.user2 = User.objects.create_user(username='test2', password='T3Ss$tTx')
        self.question = Question.objects.create(title="Lorem ipsum?", text="Lorem ipsum.", creation_time=timezone.now(), owner=self.user)

    def test_can_access_delete_question_as_owner(self):
        """
         Checks if question owner can access delete page
        """
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:question_delete', args=(self.question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_cannot_access_delete_question_not_owner(self):
        """
         Checks if regular user can't access someone's question delete page
        """
        self.client.login(username='test2', password='T3Ss$tTx')
        url = reverse('questions:question_delete', args=(self.question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_can_delete_question_as_owner(self):
        """
         Checks if question owner can actually delete question 
        """
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:question_delete', args=(self.question.id,))
        response = self.client.post(url)
        with self.assertRaises(Question.DoesNotExist):
            Question.objects.get(pk=self.question.id)

    def test_cannot_delete_question_not_owner(self):
        """
         Tests if regular user cannot delete question 
        """
        self.client.login(username='test2', password='T3Ss$tTx')
        url = reverse('questions:question_delete', args=(self.question.id,))
        response = self.client.post(url)
        notremoved = Question.objects.get(pk=self.question.id)
        self.assertEquals(notremoved.title, self.question.title)
        self.assertEquals(notremoved.text, self.question.text)

    def test_can_delete_question_with_tags(self):
        self.client.login(username='test', password='T3Ss$tTx')
        question = Question.objects.create(title='test with tags', text='tags are awesome', creation_time=timezone.now(), owner=self.user)
        question.tags.create(name='test')
        question.tags.create(name='lorem ipsum')

        url = reverse('questions:question_delete', args=(question.id,))
        response = self.client.post(url)
        with self.assertRaises(Question.DoesNotExist):
            Question.objects.get(pk=question.id)

class AnswerEditViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='T3Ss$tTx')
        self.user2 = User.objects.create_user(username='test2', password='T3Ss$tTx')
        self.question = Question.objects.create(title="Lorem ipsum?", text="Lorem ipsum.", creation_time=timezone.now(), owner=self.user)

    def test_can_access_edit_answer_as_owner(self):
        """
         Checks if answer owner can access edit page 
        """
        answer = _create_answer('Dolorem', self.question, self.user)
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:answer_edit', args=(self.question.id, answer.id))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_cannot_access_edit_answer_not_owner(self):
        """
         Checks if regular user can't access someone's answer edit page 
        """
        answer = _create_answer('Dolorem', self.question, self.user)
        self.client.login(username='test2', password='T3Ss$tTx')
        url = reverse('questions:answer_edit', args=(self.question.id, answer.id))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_can_edit_answer_as_owner(self):
        """
         Tests if answer owner can actually update answer 
        """
        answer = _create_answer('test', self.question, self.user)
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:answer_edit', args=(self.question.id, answer.id,))
        response = self.client.post(url, {'text': 'testtesttest'})
        updated = Answer.objects.get(pk=answer.id)
        self.assertEqual(updated.text, 'testtesttest')

    def test_cannot_edit_answer_not_owner(self):
        """
         Tests if regular user cannot update answer
        """
        answer = _create_answer('test', self.question, self.user)
        self.client.login(username='test2', password='T3Ss$tTx')
        url = reverse('questions:answer_edit', args=(self.question.id, answer.id))
        response = self.client.post(url, {'text': 'Lorem ipsum dolor'})
        notupdated = Answer.objects.get(pk=answer.id)
        self.assertEqual(notupdated.text, answer.text)

class AnswerDeleteViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='T3Ss$tTx')
        self.user2 = User.objects.create_user(username='test2', password='T3Ss$tTx')
        self.question = Question.objects.create(title="Lorem ipsum?", text="Lorem ipsum.", creation_time=timezone.now(), owner=self.user)

    def test_can_access_delete_answer_as_owner(self):
        """
         Checks if answer owner can access delete page
        """
        answer = _create_answer('Dolorem', self.question, self.user)
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:answer_delete', args=(self.question.id, answer.id))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_cannot_access_delete_answer_not_owner(self):
        """
         Checks if regular user can't access someone's answer delete page
        """
        answer = _create_answer('Dolorem', self.question, self.user)
        self.client.login(username='test2', password='T3Ss$tTx')
        url = reverse('questions:answer_delete', args=(self.question.id, answer.id))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_can_delete_answer_as_owner(self):
        """
         Checks if answer owner can actually delete answer 
        """
        answer = _create_answer('test', self.question, self.user)
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:answer_delete', args=(self.question.id, answer.id,))
        response = self.client.post(url)
        with self.assertRaises(Answer.DoesNotExist):
            Answer.objects.get(pk=answer.id)

    def test_cannot_delete_answer_not_owner(self):
        """
         Tests if regular user cannot delete answer 
        """
        answer = _create_answer('test', self.question, self.user)
        self.client.login(username='test2', password='T3Ss$tTx')
        url = reverse('questions:answer_delete', args=(self.question.id, answer.id))
        response = self.client.post(url)
        notremoved = Answer.objects.get(pk=answer.id)
        self.assertEquals(notremoved.text, answer.text)

class AskViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='T3Ss$tTx')
        # self.user2 = User.objects.create_user(username='test2', password='T3Ss$tTx')

    def test_access_logged(self):
        self.client.login(username='test', password='T3Ss$tTx')
        response = self.client.get(reverse('questions:ask'))
        self.assertEqual(response.status_code, 200)

    def test_access_not_logged(self):
        response = self.client.get(reverse('questions:ask'))
        self.assertEqual(response.status_code, 302)

    def test_asking_question_logged(self):
        self.client.login(username='test', password='T3Ss$tTx')
        response = self.client.post(reverse('questions:ask'), {'title': 'test', 'text': 'lorem ipsum dolor'})
        added = Question.objects.get(title__exact='test')
        self.assertEqual(added.text, 'lorem ipsum dolor')

    def test_asking_question_with_tags_logged(self):
        self.client.login(username='test', password='T3Ss$tTx')
        Tag.objects.create(name='test')
        Tag.objects.create(name='lorem ipsum')
        response = self.client.post(reverse('questions:ask'), {'title': 'test', 'text': 'lorem ipsum dolor', 'tags': 'test, lorem ipsum'})
        added = Question.objects.get(title__exact='test')
        self.assertEqual(added.text, 'lorem ipsum dolor')
        self.assertQuerysetEqual(added.tags.all(), ["<Tag: test>", "<Tag: lorem ipsum>"], ordered=False)

    def test_asking_question_not_logged(self):
        response = self.client.post(reverse('questions:ask'), {'title': 'test', 'text': 'not added question'})
        with self.assertRaises(Question.DoesNotExist):
            Question.objects.get(title__exact='test')

class RegisterView(TestCase):

    def test_access_register(self):
        response = self.client.get(reverse('questions:register'))
        self.assertEqual(response.status_code, 200)

    def test_register(self):
        response = self.client.post(reverse('questions:register'), {'username': 'test', 'password1': 'T3Ss$tTx', 'password2': 'T3Ss$tTx', 'email': 'test@test.com'})
        registered = User.objects.get(username__exact='test')

class AnswerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='T3Ss$tTx')
        self.question = Question.objects.create(title="Lorem ipsum?", text="Lorem ipsum.", creation_time=timezone.now(), owner=self.user)

    def test_can_add_answer_logged(self):
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:answer', args=(self.question.id,))
        response = self.client.post(url, {'text': 'test answer'})
        added = Answer.objects.get(question_id=self.question.id)

    def test_raise_404_not_post(self):
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:answer', args=(self.question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_cannot_add_answer_not_loged(self):
        url = reverse('questions:answer', args=(self.question.id,))
        response = self.client.post(url, {'text': 'test answer'})
        with self.assertRaises(Answer.DoesNotExist):
            added = Answer.objects.get(question_id=self.question.id)

class UserViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='T3Ss$tTx')
        self.user2 = User.objects.create_user(username='test2', password='T3Ss$tTx')

    def test_context(self):
        url = reverse('questions:user', args=(self.user.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['profile'], self.user)

    def test_context_logged_as_owner(self):
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:user', args=(self.user.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['profile'], self.user)

    def test_context_logged_as_not_owner(self):
        self.client.login(username='test2', password='T3Ss$tTx')
        url = reverse('questions:user', args=(self.user.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['profile'], self.user)

class UserEditViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='T3Ss$tTx')
        self.user2 = User.objects.create_user(username='test2', password='T3Ss$tTx')

    def tearDown(self):
        ''' Deleting users to remove images '''
        User.objects.get(pk=self.user.id).delete()
        User.objects.get(pk=self.user2.id).delete()

    def _create_avatar(self, image_format, size=(128, 128)):
        data = BytesIO()
        Image.new('RGB', size).save(data, image_format)
        data.seek(0)
        return data

    def _get_form_values(self, user_id):
        user = User.objects.get(pk=user_id)
        profile = user.userprofile
        values = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'description': profile.description,
            'location': profile.location,
            'links': profile.links
        }
        return values

    def test_can_access_as_owner(self):
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_cannot_access_as_not_owner(self):
        self.client.login(username='test2', password='T3Ss$tTx')
        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_cannot_access_as_not_logged(self):
        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_can_update_username_as_owner(self):
        self.client.login(username='test', password='T3Ss$tTx')

        data = self._get_form_values(self.user.id)
        data['username'] = 'abcdefgh'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.username, 'abcdefgh')

    def test_can_update_first_name_as_owner(self):
        self.client.login(username='test', password='T3Ss$tTx')

        data = self._get_form_values(self.user.id)
        data['first_name'] = 'abcdefgh'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.first_name, 'abcdefgh')

    def test_can_update_last_name_as_owner(self):
        self.client.login(username='test', password='T3Ss$tTx')

        data = self._get_form_values(self.user.id)
        data['last_name'] = 'abcdefgh'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.last_name, 'abcdefgh')

    def test_can_update_avatar_as_owner(self):
        self.client.login(username='test', password='T3Ss$tTx')

        data = self._get_form_values(self.user.id)
        new_avatar = SimpleUploadedFile(name='test.png', content=open('questions/test.png', 'rb').read(), content_type='image/png')
        data['avatar'] = new_avatar

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        self.assertEqual(User.objects.get(pk=self.user.id).userprofile.avatar.name, 'avatars/' + str(self.user.id) + '.png')

    def test_can_update_description_as_owner(self):
        self.client.login(username='test', password='T3Ss$tTx')

        # Setting up post data
        data = self._get_form_values(self.user.id)
        data['description'] = 'testtesttest'
        
        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id).userprofile

        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.description, 'testtesttest')

    def test_can_update_location_as_owner(self):
        self.client.login(username='test', password='T3Ss$tTx')

        # Setting up post data
        data = self._get_form_values(self.user.id)
        data['location'] = 'testtesttest'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id).userprofile

        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.location, 'testtesttest')

    def test_can_update_links_as_owner(self):
        self.client.login(username='test', password='T3Ss$tTx')

        # Setting up post data
        data = self._get_form_values(self.user.id)
        data['links'] = 'http://google.com'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id).userprofile

        self.assertEqual(response.status_code, 302)
        self.assertListEqual(profile.links, ['http://google.com'])

    def test_cannot_update_username_as_not_owner(self):
        self.client.login(username='test2', password='T3Ss$tTx')

        data = self._get_form_values(self.user.id)
        data['username'] = 'abcdefgh'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.username, 'test')

    def test_cannot_update_first_name_as_not_owner(self):
        self.client.login(username='test2', password='T3Ss$tTx')

        data = self._get_form_values(self.user.id)
        data['first_name'] = 'abcdefgh'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.first_name, '')

    def test_cannot_update_last_name_as_not_owner(self):
        self.client.login(username='test2', password='T3Ss$tTx')

        data = self._get_form_values(self.user.id)
        data['last_name'] = 'abcdefgh'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.last_name, '')

    # def test_cannot_update_avatar_as_not_owner(self):
    #     self.client.login(username='test2', password='T3Ss$tTx')

    def test_cannot_update_description_as_not_owner(self):
        self.client.login(username='test2', password='T3Ss$tTx')

        # Setting up post data
        data = self._get_form_values(self.user.id)
        data['description'] = 'testtesttest'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id).userprofile
        self.assertEqual(profile.description, None)

    def test_cannot_update_location_as_not_owner(self):
        self.client.login(username='test2', password='T3Ss$tTx')

        # Setting up post data
        data = self._get_form_values(self.user.id)
        data['location'] = 'testtesttest'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id).userprofile
        self.assertEqual(profile.location, None)

    def test_cannot_update_links_as_not_owner(self):
        self.client.login(username='test2', password='T3Ss$tTx')

        # Setting up post data
        data = self._get_form_values(self.user.id)
        data['links'] = 'http://google.com'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id).userprofile
        self.assertEqual(profile.links, None)

    def test_cannot_update_username_as_not_logged(self):
        data = self._get_form_values(self.user.id)
        data['username'] = 'abcdefgh'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.username, 'test')

    def test_cannot_update_first_name_as_not_logged(self):
        data = self._get_form_values(self.user.id)
        data['first_name'] = 'abcdefgh'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.first_name, '')

    def test_cannot_update_last_name_as_not_logged(self):
        data = self._get_form_values(self.user.id)
        data['last_name'] = 'abcdefgh'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(profile.last_name, '')

    # def test_cannot_update_avatar_as_not_logged(self):
    #     pass

    def test_cannot_update_description_as_not_logged(self):
        # Setting up post data
        data = self._get_form_values(self.user.id)
        data['description'] = 'testtesttest'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id).userprofile
        self.assertEqual(profile.description, None)

    def test_cannot_update_location_as_not_logged(self):
        # Setting up post data
        data = self._get_form_values(self.user.id)
        data['location'] = 'testtesttest'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id).userprofile
        self.assertEqual(profile.location, None)

    def test_cannot_update_links_as_not_logged(self):
        # Setting up post data
        data = self._get_form_values(self.user.id)
        data['links'] = 'http://google.com'

        url = reverse('questions:user_edit', args=(self.user.id,))
        response = self.client.post(url, data)
        profile = User.objects.get(pk=self.user.id).userprofile
        self.assertEqual(profile.links, None)

class AccountSettingsTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='T3Ss$tTx')
        self.user2 = User.objects.create_user(username='test2', password='T3Ss$tTx')

    def test_can_change_own_password(self):
        self.client.login(username='test', password='T3Ss$tTx')
        url = reverse('questions:user_settings', args=(self.user.id,))
        response = self.client.post(url, {'action': 'change_password', 'old_password': 'T3Ss$tTx', 'new_password1': 'T3Ss$tTx2', 'new_password2': 'T3Ss$tTx2'})
        self.client.logout()
        self.assertIs(self.client.login(username='test', password='T3Ss$tTx'), False)
        self.assertIs(self.client.login(username='test', password='T3Ss$tTx2'), True)

class SearchViewTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='T3Ss$tTx')
        self.user2 = User.objects.create_user(username='test2', password='T3Ss$tTx')
        self.question = Question.objects.create(title="How do I do that", text="Lorem ipsum dolor sit amet consectetur adipiscing elit.",
                        creation_time=timezone.now(), owner=self.user)
        self.question2 = Question.objects.create(title="Lorem ipsum dolor sit amet", text="test test test test test test test test test test",
                creation_time=timezone.now(), owner=self.user)

    def test_search_nothing(self):
        response = self.client.get(reverse('questions:search'), {'q': 'qwerty'})
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['questions'], [])

    def test_search_title_or_text(self):
        response = self.client.get(reverse('questions:search'), {'q': 'Lorem ipsum'})
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['questions'], ['<Question: How do I do that>', '<Question: Lorem ipsum dolor sit amet>'], ordered=False)

class TaggedViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='T3Ss$tTx')
        self.user2 = User.objects.create_user(username='test2', password='T3Ss$tTx')
        self.question1 = Question.objects.create(title="How do I do that", text="Lorem ipsum dolor sit amet consectetur adipiscing elit.",
                        creation_time=timezone.now(), owner=self.user)
        self.question2 = Question.objects.create(title="Lorem ipsum dolor sit amet", text="test test test test test test test test test test",
                creation_time=timezone.now(), owner=self.user)
        self.tags1 = [
            {'name': 'lorem ipsum'},
            {'name': 'test'},
            {'name': 'question1'}
        ]
        for tag in self.tags1:
            self.question1.tags.create(**tag)
        self.tags2 = [
            {'name': 'tagged'},
            {'name': 'question2'}
        ]
        for tag in self.tags2:
            self.question2.tags.create(**tag)
        self.question2.tags.add(Tag.objects.get(name__exact='lorem ipsum'))

    def test_show_nothing(self):
        response = self.client.get(reverse('questions:tagged', args=('qwerty',)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['questions'], [])
    
    def test_standard_tag_search(self):
        response = self.client.get(reverse('questions:tagged', args=('lorem ipsum',)))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['questions'], ["<Question: How do I do that>", "<Question: Lorem ipsum dolor sit amet>"], ordered=False)
