from django.db import models
from django.core.exceptions import ValidationError

class Client(models.Model):
    name = models.CharField(verbose_name='Name', max_length=100)
    email = models.EmailField(verbose_name='Email')
    age = models.PositiveIntegerField(verbose_name='Age')

    def __str__(self):
        return f'Client: {self.name}'

    def verify_age(self):
        """
        Verify if client is at leat 18 years old.
        Raises ValidationError if Client is underage.
        """
        if self.age<18:
            raise ValidationError('We do not accept clients under 18 years old.')
