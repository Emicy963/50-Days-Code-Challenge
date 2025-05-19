from django.db import models

class Client(models.Model):
    name = models.CharField(verbose_name='Name', max_length=100)
    email = models.EmailField(verbose_name='Email')
    age = models.PositiveIntegerField(verbose_name='Age')

    def __str__(self):
        return f'Client: {self.name}'
