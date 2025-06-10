from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Pedido
from clients.models import Client

class PedidoForm(forms.ModelForm):
    """
    Formulário para criação e edição de pedidos
    """

    class Meta:
        model = Pedido
        fields = [
            "cliente",
            "descricao",
            "valor_total",
            "status",
            "prioridade",
            "data_entrega_prevista",
            "observacoes",
        ]
        widgets = {
            "descricao": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Descreva detalhadamente o pedido..."}
            ),
            "data_entrega_prevista": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "observacoes": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Observações adicionais (opcional)..."}
            ),
            "valor_total": forms.NumberInput(
                attrs={"step": "0.01", "min": "0", "placeholder": "0.00"}
            ),
            "cliente": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "prioridade": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar clientes por nome
        self.fields["cliente"].queryset = Client.objects.all().order_by("name")

        # Definir labels e help_text personalizados
        self.fields["cliente"].empty_label = "Selecione um cliente"

        # Tornar campos obrigatórios mais claros
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs["class"] = (
                    field.widget.attrs.get("class", "") + " required"
                )

    def clean_data_entrega_prevista(self):
        """
        Validar se a data de entrega prevista não é no passado
        """
        data = self.cleaned_data.get("data_entrega_prevista")
        if data and data < timezone.now().date():
            raise ValidationError("A data de entrega prevista não pode ser no passado.")
        return data

    def clean_valor_total(self):
        """
        Validar se o valor total é positivo
        """
        valor = self.cleaned_data.get("valor_total")
        if valor is not None and valor < 0:
            raise ValidationError("O valor total deve ser positivo.")
        return valor


class PedidoSearchForm(forms.Form):
    """
    Formulário para busca e filtros de pedidos
    """

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Buscar por número do pedido, cliente ou descrição...",
                "class": "form-control",
            }
        ),
        label="Buscar",
    )

    cliente = forms.ModelChoiceField(
        queryset=Client.objects.all().order_by("name"),
        required=False,
        empty_label="Todos os clientes",
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Cliente",
    )

    status = forms.ChoiceField(
        choices=[("", "Todos os status")] + Pedido.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Status",
    )

    prioridade = forms.ChoiceField(
        choices=[("", "Todas as prioridades")] + Pedido.PRIORIDADE_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Prioridade",
    )

    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Data de início",
    )

    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Data de fim",
    )

    valor_min = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(
            attrs={
                "step": "0.01",
                "min": "0",
                "placeholder": "0.00",
                "class": "form-control",
            }
        ),
        label="Valor mínimo",
    )

    valor_max = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(
            attrs={
                "step": "0.01",
                "min": "0",
                "placeholder": "0.00",
                "class": "form-control",
            }
        ),
        label="Valor máximo",
    )

    def clean(self):
        """
        Validações cruzadas do formulário
        """
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get("data_inicio")
        data_fim = cleaned_data.get("data_fim")
        valor_min = cleaned_data.get("valor_min")
        valor_max = cleaned_data.get("valor_max")

        # Validar intervalo de datas
        if data_inicio and data_fim and data_inicio > data_fim:
            raise ValidationError(
                "A data de início não pode ser posterior à data de fim."
            )

        # Validar intervalo de valores
        if valor_min is not None and valor_max is not None and valor_min > valor_max:
            raise ValidationError(
                "O valor mínimo não pode ser maior que o valor máximo."
            )

        return cleaned_data


class PedidoStatusForm(forms.Form):
    """
    Formulário simples para atualização rápida de status
    """

    status = forms.ChoiceField(
        choices=Pedido.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Novo Status",
    )

    observacao = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 2,
                "placeholder": "Observação sobre a mudança de status (opcional)...",
                "class": "form-control",
            }
        ),
        label="Observação",
    )


class PedidoBulkActionForm(forms.Form):
    """
    Formulário para ações em lote
    """

    ACTION_CHOICES = [
        ("", "Selecione uma ação"),
        ("update_status", "Atualizar Status"),
        ("update_priority", "Atualizar Prioridade"),
        ("delete", "Excluir Pedidos"),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Ação",
    )

    new_status = forms.ChoiceField(
        choices=Pedido.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Novo Status",
    )

    new_priority = forms.ChoiceField(
        choices=Pedido.PRIORIDADE_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Nova Prioridade",
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get("action")

        if action == "update_status" and not cleaned_data.get("new_status"):
            raise ValidationError("Selecione o novo status.")

        if action == "update_priority" and not cleaned_data.get("new_priority"):
            raise ValidationError("Selecione a nova prioridade.")

        return cleaned_data
