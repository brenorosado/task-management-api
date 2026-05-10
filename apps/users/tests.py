from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from apps.users.models import User
from apps.users.validators import UppercaseValidator, LowercaseValidator, NumberValidator, SpecialCharValidator


class UserManagerTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user('john@example.com', 'John', 'Password1!')
        self.assertEqual(user.email, 'john@example.com')
        self.assertEqual(user.name, 'John')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_create_user_password_is_hashed(self):
        user = User.objects.create_user('john@example.com', 'John', 'Password1!')
        self.assertNotEqual(user.password, 'Password1!')
        self.assertTrue(user.check_password('Password1!'))

    def test_create_superuser(self):
        user = User.objects.create_superuser('admin@example.com', 'Admin', 'Password1!')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_user_str(self):
        user = User.objects.create_user('john@example.com', 'John', 'Password1!')
        self.assertEqual(str(user), 'john@example.com')


class PasswordValidatorTests(TestCase):
    def test_uppercase_validator_passes(self):
        UppercaseValidator().validate('Password1!')

    def test_uppercase_validator_fails(self):
        with self.assertRaises(ValidationError):
            UppercaseValidator().validate('password1!')

    def test_lowercase_validator_passes(self):
        LowercaseValidator().validate('Password1!')

    def test_lowercase_validator_fails(self):
        with self.assertRaises(ValidationError):
            LowercaseValidator().validate('PASSWORD1!')

    def test_number_validator_passes(self):
        NumberValidator().validate('Password1!')

    def test_number_validator_fails(self):
        with self.assertRaises(ValidationError):
            NumberValidator().validate('Password!')

    def test_special_char_validator_passes(self):
        SpecialCharValidator().validate('Password1!')

    def test_special_char_validator_fails(self):
        with self.assertRaises(ValidationError):
            SpecialCharValidator().validate('Password1')


class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/users/register'
        self.valid_payload = {
            'email': 'john@example.com',
            'name': 'John',
            'password': 'Xk9#mP2$qR7!',
        }

    def test_register_success(self):
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, 201)

    def test_register_duplicate_email(self):
        self.client.post(self.url, self.valid_payload)
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, 400)

    def test_register_missing_email(self):
        payload = {**self.valid_payload, 'email': ''}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 400)

    def test_register_missing_name(self):
        payload = {**self.valid_payload, 'name': ''}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 400)

    def test_register_weak_password(self):
        payload = {**self.valid_payload, 'password': 'weak'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 400)


class SelfViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('john@example.com', 'John', 'Password1!')

    def test_self_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/users/self')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'john@example.com')
        self.assertEqual(response.data['name'], 'John')

    def test_self_unauthenticated(self):
        response = self.client.get('/api/users/self')
        self.assertEqual(response.status_code, 401)
