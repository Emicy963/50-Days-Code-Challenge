from django import forms
from django.core.exceptions import ValidationError
from .models import Client
import re


class ClientForm(forms.ModelForm):
    """
    ModelForm para o modelo Client com validações personalizadas
    """

    class Meta:
        model = Client
        fields = ["name", "email", "age"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "Digite o nome completo",
                    "maxlength": 100,
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "placeholder": "exemplo@email.com",
                }
            ),
            "age": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                    "min": 18,
                    "max": 120,
                    "placeholder": "Idade (mínimo 18 anos)",
                }
            ),
        }
        labels = {
            "name": "Nome Completo",
            "email": "Endereço de Email",
            "age": "Idade",
        }
        help_texts = {
            "name": "Digite o nome completo do cliente",
            "email": "Insira um endereço de email válido",
            "age": "Idade mínima permitida: 18 anos",
        }

    def clean_name(self):
        """
        Validação personalizada para o campo name
        """
        name = self.cleaned_data.get("name")

        if not name:
            raise ValidationError("Nome é obrigatório.")

        # Verificar se contém apenas letras e espaços
        if not re.match(r"^[a-zA-ZÀ-ÿ\s]+$", name):
            raise ValidationError("Nome deve conter apenas letras e espaços.")

        # Verificar comprimento mínimo
        if len(name.strip()) < 2:
            raise ValidationError("Nome deve ter pelo menos 2 caracteres.")

        # Verificar se não é apenas espaços
        if not name.strip():
            raise ValidationError("Nome não pode conter apenas espaços.")

        # Capitalizar cada palavra
        return name.title().strip()

    def clean_email(self):
        """
        Validação personalizada para o campo email
        """
        email = self.cleaned_data.get("email")

        if not email:
            raise ValidationError("Email é obrigatório.")

        # Verificar se email já existe (exceto se for update)
        existing_client = Client.objects.filter(email=email).first()
        if existing_client:
            # Se estamos editando, permitir o mesmo email
            if hasattr(self, "instance") and self.instance.pk:
                if existing_client.pk != self.instance.pk:
                    raise ValidationError(
                        "Este email já está sendo usado por outro cliente."
                    )
            else:
                raise ValidationError("Este email já está cadastrado.")

        # Verificar domínios proibidos (exemplo)
        forbidden_domains = ["tempmail.com", "10minutemail.com", "guerrillamail.com"]
        domain = email.split("@")[1].lower() if "@" in email else ""
        if domain in forbidden_domains:
            raise ValidationError("Este domínio de email não é permitido.")

        return email.lower()

    def clean_age(self):
        """
        Validação personalizada para o campo age
        """
        age = self.cleaned_data.get("age")

        if age is None:
            raise ValidationError("Idade é obrigatória.")

        if age < 18:
            raise ValidationError("Não aceitamos clientes menores de 18 anos.")

        if age > 120:
            raise ValidationError("Idade deve ser realista (máximo 120 anos).")

        return age

    def clean(self):
        """
        Validação geral do formulário
        """
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        age = cleaned_data.get("age")

        # Validação combinada: se nome sugere idade jovem mas idade é alta
        if name and age:
            youth_indicators = ["junior", "jr", "filho", "neto"]
            if (
                any(indicator in name.lower() for indicator in youth_indicators)
                and age > 80
            ):
                raise ValidationError(
                    "Há uma inconsistência entre o nome e a idade informada."
                )

        return cleaned_data


class ClientSearchForm(forms.Form):
    """
    Formulário para busca de clientes
    """

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                "placeholder": "Buscar por nome ou email...",
            }
        ),
        label="Buscar Cliente",
    )

    age_min = forms.IntegerField(
        required=False,
        min_value=18,
        max_value=120,
        widget=forms.NumberInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                "placeholder": "Idade mínima",
            }
        ),
        label="Idade Mínima",
    )

    age_max = forms.IntegerField(
        required=False,
        min_value=18,
        max_value=120,
        widget=forms.NumberInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500",
                "placeholder": "Idade máxima",
            }
        ),
        label="Idade Máxima",
    )

    def clean(self):
        """
        Validação para garantir que idade mínima não seja maior que máxima
        """
        cleaned_data = super().clean()
        age_min = cleaned_data.get("age_min")
        age_max = cleaned_data.get("age_max")

        if age_min and age_max and age_min > age_max:
            raise ValidationError("Idade mínima não pode ser maior que idade máxima.")

        return cleaned_data
