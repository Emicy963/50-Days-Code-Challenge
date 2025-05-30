from datetime import timezone
from django import forms
from django.core.exceptions import ValidationError
from .models import Client, Pedido
import re

class ClientForm(forms.ModelForm):
    """
    ModelForm para o modelo Client com validações personalizadas
    """  
    class Meta:
        model = Client
        fields = ['name', 'email', 'age']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Digite o nome completo',
                'maxlength': 100,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'exemplo@email.com',
            }),
            'age': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'min': 18,
                'max': 120,
                'placeholder': 'Idade (mínimo 18 anos)',
            }),
        }
        labels = {
            'name': 'Nome Completo',
            'email': 'Endereço de Email',
            'age': 'Idade',
        }
        help_texts = {
            'name': 'Digite o nome completo do cliente',
            'email': 'Insira um endereço de email válido',
            'age': 'Idade mínima permitida: 18 anos',
        }

    def clean_name(self):
        """
        Validação personalizada para o campo name
        """
        name = self.cleaned_data.get('name')
        
        if not name:
            raise ValidationError('Nome é obrigatório.')
        
        # Verificar se contém apenas letras e espaços
        if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', name):
            raise ValidationError('Nome deve conter apenas letras e espaços.')
        
        # Verificar comprimento mínimo
        if len(name.strip()) < 2:
            raise ValidationError('Nome deve ter pelo menos 2 caracteres.')
        
        # Verificar se não é apenas espaços
        if not name.strip():
            raise ValidationError('Nome não pode conter apenas espaços.')
        
        # Capitalizar cada palavra
        return name.title().strip()

    def clean_email(self):
        """
        Validação personalizada para o campo email
        """
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError('Email é obrigatório.')
        
        # Verificar se email já existe (exceto se for update)
        existing_client = Client.objects.filter(email=email).first()
        if existing_client:
            # Se estamos editando, permitir o mesmo email
            if hasattr(self, 'instance') and self.instance.pk:
                if existing_client.pk != self.instance.pk:
                    raise ValidationError('Este email já está sendo usado por outro cliente.')
            else:
                raise ValidationError('Este email já está cadastrado.')
        
        # Verificar domínios proibidos (exemplo)
        forbidden_domains = ['tempmail.com', '10minutemail.com', 'guerrillamail.com']
        domain = email.split('@')[1].lower() if '@' in email else ''
        if domain in forbidden_domains:
            raise ValidationError('Este domínio de email não é permitido.')
        
        return email.lower()

    def clean_age(self):
        """
        Validação personalizada para o campo age
        """
        age = self.cleaned_data.get('age')
        
        if age is None:
            raise ValidationError('Idade é obrigatória.')
        
        if age < 18:
            raise ValidationError('Não aceitamos clientes menores de 18 anos.')
        
        if age > 120:
            raise ValidationError('Idade deve ser realista (máximo 120 anos).')
        
        return age

    def clean(self):
        """
        Validação geral do formulário
        """
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        age = cleaned_data.get('age')
        
        # Validação combinada: se nome sugere idade jovem mas idade é alta
        if name and age:
            youth_indicators = ['junior', 'jr', 'filho', 'neto']
            if any(indicator in name.lower() for indicator in youth_indicators) and age > 80:
                raise ValidationError('Há uma inconsistência entre o nome e a idade informada.')
        
        return cleaned_data

class ClientSearchForm(forms.Form):
    """
    Formulário para busca de clientes
    """
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Buscar por nome ou email...',
        }),
        label='Buscar Cliente'
    )
    
    age_min = forms.IntegerField(
        required=False,
        min_value=18,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Idade mínima',
        }),
        label='Idade Mínima'
    )
    
    age_max = forms.IntegerField(
        required=False,
        min_value=18,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Idade máxima',
        }),
        label='Idade Máxima'
    )

    def clean(self):
        """
        Validação para garantir que idade mínima não seja maior que máxima
        """
        cleaned_data = super().clean()
        age_min = cleaned_data.get('age_min')
        age_max = cleaned_data.get('age_max')
        
        if age_min and age_max and age_min > age_max:
            raise ValidationError('Idade mínima não pode ser maior que idade máxima.')
        
        return cleaned_data

class PedidoForm(forms.ModelForm):
    """
    Formulário para criação e edição de pedidos
    """
    class Meta:
        model = Pedido
        fields = [
            'cliente', 'descricao', 'valor_total', 'status', 
            'prioridade', 'data_entrega_prevista', 'observacoes'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Descreva detalhadamente o pedido...'
            }),
            'data_entrega_prevista': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'observacoes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Observações adicionais (opcional)...'
            }),
            'valor_total': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'prioridade': forms.Select(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar clientes por nome
        self.fields['cliente'].queryset = Client.objects.all().order_by('name')
        
        # Definir labels e help_text personalizados
        self.fields['cliente'].empty_label = "Selecione um cliente"
        
        # Tornar campos obrigatórios mais claros
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' required'
    
    def clean_data_entrega_prevista(self):
        """
        Validar se a data de entrega prevista não é no passado
        """
        data = self.cleaned_data.get('data_entrega_prevista')
        if data and data < timezone.now().date():
            raise ValidationError('A data de entrega prevista não pode ser no passado.')
        return data

    def clean_valor_total(self):
        """
        Validar se o valor total é positivo
        """
        valor = self.cleaned_data.get('valor_total')
        if valor is not None and valor < 0:
            raise ValidationError('O valor total deve ser positivo.')
        return valor

class PedidoSearchForm(forms.Form):
    """
    Formulário para busca e filtros de pedidos
    """
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por número do pedido, cliente ou descrição...',
            'class': 'form-control'
        }),
        label='Buscar'
    )
    
    cliente = forms.ModelChoiceField(
        queryset=Client.objects.all().order_by('name'),
        required=False,
        empty_label="Todos os clientes",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Cliente'
    )
    
    status = forms.ChoiceField(
        choices=[('', 'Todos os status')] + Pedido.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Status'
    )
    
    prioridade = forms.ChoiceField(
        choices=[('', 'Todas as prioridades')] + Pedido.PRIORIDADE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Prioridade'
    )
    
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Data de início'
    )
    
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Data de fim'
    )
    
    valor_min = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00',
            'class': 'form-control'
        }),
        label='Valor mínimo'
    )
    
    valor_max = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00',
            'class': 'form-control'
        }),
        label='Valor máximo'
    )
    