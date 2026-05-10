import re
from django.core.exceptions import ValidationError

class UppercaseValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter.')

    def get_help_text(self):
        return 'Password must contain at least one uppercase letter.'

class LowercaseValidator:
    def validate(self, password, user=None):
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter.')

    def get_help_text(self):
        return 'Password must contain at least one lowercase letter.'

class NumberValidator:
    def validate(self, password, user=None):
        if not re.search(r'[0-9]', password):
            raise ValidationError('Password must contain at least one number.')

    def get_help_text(self):
        return 'Password must contain at least one number.'

class SpecialCharValidator:
    def validate(self, password, user=None):
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Password must contain at least one special character.')

    def get_help_text(self):
        return 'Password must contain at least one special character.'
