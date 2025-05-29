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

class Pedido(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('processando', 'Processando'),
        ('enviado', 'Enviado'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    cliente = models.ForeignKey(
        'Client',  # Referência ao modelo Client
        on_delete=models.CASCADE,
        related_name='pedidos',
        verbose_name='Cliente',
        help_text='Cliente que fez o pedido'
    )
    
    numero_pedido = models.CharField(
        verbose_name='Número do Pedido',
        max_length=20,
        unique=True,
        help_text='Número único do pedido (gerado automaticamente)'
    )
    
    descricao = models.TextField(
        verbose_name='Descrição',
        help_text='Descrição detalhada do pedido'
    )
    
    valor_total = models.DecimalField(
        verbose_name='Valor Total',
        max_digits=10,
        decimal_places=2,
        help_text='Valor total do pedido em reais'
    )
    
    status = models.CharField(
        verbose_name='Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        help_text='Status atual do pedido'
    )
    
    prioridade = models.CharField(
        verbose_name='Prioridade',
        max_length=10,
        choices=PRIORIDADE_CHOICES,
        default='media',
        help_text='Nível de prioridade do pedido'
    )
    
    data_pedido = models.DateTimeField(
        verbose_name='Data do Pedido',
        auto_now_add=True,
        help_text='Data e hora em que o pedido foi criado'
    )
    
    data_entrega_prevista = models.DateField(
        verbose_name='Data de Entrega Prevista',
        null=True,
        blank=True,
        help_text='Data prevista para entrega do pedido'
    )
    
    data_entrega_realizada = models.DateTimeField(
        verbose_name='Data de Entrega Realizada',
        null=True,
        blank=True,
        help_text='Data e hora em que o pedido foi efetivamente entregue'
    )
    
    observacoes = models.TextField(
        verbose_name='Observações',
        blank=True,
        help_text='Observações adicionais sobre o pedido'
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
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-data_pedido']  # Mais recentes primeiro
        indexes = [
            models.Index(fields=['numero_pedido']),
            models.Index(fields=['cliente', 'status']),
            models.Index(fields=['data_pedido']),
            models.Index(fields=['status']),
            models.Index(fields=['prioridade']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(valor_total__gte=0),
                name='valor_total_positivo'
            )
        ]

    def __str__(self):
        return f'Pedido {self.numero_pedido} - {self.cliente.name}'

    def clean(self):
        """
        Validações customizadas do modelo
        """
        super().clean()
        
        # Validar valor total
        if self.valor_total is not None and self.valor_total < 0:
            raise ValidationError({
                'valor_total': 'O valor total não pode ser negativo.'
            })
        
        # Validar data de entrega prevista
        if self.data_entrega_prevista:
            from django.utils import timezone
            if self.data_entrega_prevista < timezone.now().date():
                raise ValidationError({
                    'data_entrega_prevista': 'A data de entrega prevista não pode ser no passado.'
                })
        
        # Validar status e data de entrega
        if self.status == 'entregue' and not self.data_entrega_realizada:
            raise ValidationError({
                'data_entrega_realizada': 'Data de entrega realizada é obrigatória para pedidos entregues.'
            })
        
        # Validar descrição mínima
        if self.descricao and len(self.descricao.strip()) < 10:
            raise ValidationError({
                'descricao': 'Descrição deve ter pelo menos 10 caracteres.'
            })

