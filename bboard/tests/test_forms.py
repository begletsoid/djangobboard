from django.test import TestCase, RequestFactory

from main.forms import RegisterUserForm
from main.models import AdvUser

class RegisterUserFormTest(TestCase):
    
    def test_password_mismatch(self):
        form_data = {'username' : 'Alex', 'first_name' : 'Alexander',
                               'last_name' : 'Smith', 'email' : 'alex@gmail.com',
                               'password1' : 'Test1111', 'password2' : 'Test2111'}
        form = RegisterUserForm(data = form_data)
        self.assertFalse(form.is_valid())

    def test_password_match(self):
        form_data = {'username' : 'Alex', 'first_name' : 'Alexander',
                               'last_name' : 'Smith', 'email' : 'alex@gmail.com',
                               'password1' : 'Test1111', 'password2' : 'Test1111'}
        form = RegisterUserForm(data = form_data)
        self.assertTrue(form.is_valid())

    def test_user_save(self):
        form_data = {'username' : 'Alex', 'first_name' : 'Alexander',
                               'last_name' : 'Smith', 'email' : 'alex@gmail.com',
                               'password1' : 'Test1111', 'password2' : 'Test1111'}
        form = RegisterUserForm(data = form_data)
        form.save()
        self.assertTrue(self.client.login(username = 'Alex', password = 'Test1111'))
