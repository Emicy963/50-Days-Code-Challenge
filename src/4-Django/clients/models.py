from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse

class Client(models.Model):
    name = models.CharField(
        verbose_name='Nome', 
        max_length=100,
        help_text='Nome completo do cliente'
    )
    email = models.EmailField(
        verbose_name='Email',
        unique=True,
        help_text='Endereço de email único'
    )
    age = models.PositiveIntegerField(
        verbose_name='Idade',
        help_text='Idade em anos (mínimo 18)'
    )
    created_at = models.DateTimeField(
        verbose_name='Criado em',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name='Atualizado em',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['email']),
            models.Index(fields=['age']),
        ]

    def __str__(self):
        return f'{self.name} ({self.email})'

    def validation_age(self):
        """
        Verificar se o cliente tem pelo menos 18 anos.
        Levanta ValidationError se o cliente for menor de idade.
        """
        if self.age < 18:
            raise ValidationError(
                'Não aceitamos clientes menores de 18 anos.',
                code='underage'
            )

    def clean(self):
        """
        Override do método clean para validações do modelo.
        Será chamado automaticamente ao usar ModelForms e .full_clean()
        """
        super().clean()
        self.validation_age()
        
        # Validação adicional do nome
        if self.name and len(self.name.strip()) < 2:
            raise ValidationError({
                'name': 'Nome deve ter pelo menos 2 caracteres.'
            })

    def save(self, *args, **kwargs):
        """
        Override do método save para garantir validação antes de salvar
        """
        self.validation_age()
        self.full_clean()  # Chama clean() e outras validações
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Retorna a URL para visualizar este cliente
        """
        return reverse('detail_client', kwargs={'id': self.pk})

    def get_age_group(self):
        """
        Retorna a faixa etária do cliente
        """
        if self.age < 25:
            return 'Jovem Adulto'
        elif self.age < 40:
            return 'Adulto'
        elif self.age < 60:
            return 'Adulto Maduro'
        else:
            return 'Idoso'

    @property
    def display_name(self):
        """
        Propriedade para exibir nome formatado
        """
        return self.name.title() if self.name else ''

    @classmethod
    def get_age_statistics(cls):
        """
        Método de classe para obter estatísticas de idade
        """
        from django.db.models import Avg, Min, Max, Count
        
        stats = cls.objects.aggregate(
            total_clients=Count('id'),
            avg_age=Avg('age'),
            min_age=Min('age'),
            max_age=Max('age')
        )
        
        return {
            'total': stats['total_clients'] or 0,
            'average_age': round(stats['avg_age'], 1) if stats['avg_age'] else 0,
            'youngest': stats['min_age'] or 0,
            'oldest': stats['max_age'] or 0,
        }