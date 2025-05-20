from django.db import models
from django.core.exceptions import ValidationError

class Client(models.Model):
    name = models.CharField(verbose_name='Name', max_length=100)
    email = models.EmailField(verbose_name='Email')
    age = models.PositiveIntegerField(verbose_name='Age')

    def __str__(self):
        return f'Client: {self.name}'

    def validation_age(self):
        """
        Verify if client is at leat 18 years old.
        Raises ValidationError if Client is underage.
        """
        if self.age<18:
            raise ValidationError('We do not accept clients under 18 years old.')
    
    def clean(self):
        """
        Override clean method to perform model validation.
        This will be called automatically when using model forms and .full_clean()
        """
        super().clean()
        self.validation_age()

    def save(self, *args, **kwargs):
        """
        Override save method to ensure age validation before saving
        """
        self.validation_age
        super().save(*args, **kwargs)
