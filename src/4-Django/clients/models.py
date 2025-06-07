from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse
from decimal import Decimal


class Client(models.Model):
    name = models.CharField(
        verbose_name="Nome", max_length=100, help_text="Nome completo do cliente"
    )
    email = models.EmailField(
        verbose_name="Email", unique=True, help_text="Endereço de email único"
    )
    age = models.PositiveIntegerField(
        verbose_name="Idade", help_text="Idade em anos (mínimo 18)"
    )
    created_at = models.DateTimeField(verbose_name="Criado em", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["email"]),
            models.Index(fields=["age"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.email})"

    def validation_age(self):
        """
        Verificar se o cliente tem pelo menos 18 anos.
        Levanta ValidationError se o cliente for menor de idade.
        """
        if self.age < 18:
            raise ValidationError(
                "Não aceitamos clientes menores de 18 anos.", code="underage"
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
            raise ValidationError({"name": "Nome deve ter pelo menos 2 caracteres."})

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
        return reverse("detail_client", kwargs={"id": self.pk})

    def get_age_group(self):
        """
        Retorna a faixa etária do cliente
        """
        if self.age < 25:
            return "Jovem Adulto"
        elif self.age < 40:
            return "Adulto"
        elif self.age < 60:
            return "Adulto Maduro"
        else:
            return "Idoso"

    @property
    def display_name(self):
        """
        Propriedade para exibir nome formatado
        """
        return self.name.title() if self.name else ""

    @classmethod
    def get_age_statistics(cls):
        """
        Método de classe para obter estatísticas de idade
        """
        from django.db.models import Avg, Min, Max, Count

        stats = cls.objects.aggregate(
            total_clients=Count("id"),
            avg_age=Avg("age"),
            min_age=Min("age"),
            max_age=Max("age"),
        )

        return {
            "total": stats["total_clients"] or 0,
            "average_age": round(stats["avg_age"], 1) if stats["avg_age"] else 0,
            "youngest": stats["min_age"] or 0,
            "oldest": stats["max_age"] or 0,
        }


class Pedido(models.Model):
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("processando", "Processando"),
        ("enviado", "Enviado"),
        ("entregue", "Entregue"),
        ("cancelado", "Cancelado"),
    ]

    PRIORIDADE_CHOICES = [
        ("baixa", "Baixa"),
        ("media", "Média"),
        ("alta", "Alta"),
        ("urgente", "Urgente"),
    ]

    cliente = models.ForeignKey(
        "Client",  # Referência ao modelo Client
        on_delete=models.CASCADE,
        related_name="pedidos",
        verbose_name="Cliente",
        help_text="Cliente que fez o pedido",
    )

    numero_pedido = models.CharField(
        verbose_name="Número do Pedido",
        max_length=20,
        unique=True,
        help_text="Número único do pedido (gerado automaticamente)",
    )

    descricao = models.TextField(
        verbose_name="Descrição", help_text="Descrição detalhada do pedido"
    )

    valor_total = models.DecimalField(
        verbose_name="Valor Total",
        max_digits=10,
        decimal_places=2,
        help_text="Valor total do pedido em reais",
    )

    status = models.CharField(
        verbose_name="Status",
        max_length=20,
        choices=STATUS_CHOICES,
        default="pendente",
        help_text="Status atual do pedido",
    )

    prioridade = models.CharField(
        verbose_name="Prioridade",
        max_length=10,
        choices=PRIORIDADE_CHOICES,
        default="media",
        help_text="Nível de prioridade do pedido",
    )

    data_pedido = models.DateTimeField(
        verbose_name="Data do Pedido",
        auto_now_add=True,
        help_text="Data e hora em que o pedido foi criado",
    )

    data_entrega_prevista = models.DateField(
        verbose_name="Data de Entrega Prevista",
        null=True,
        blank=True,
        help_text="Data prevista para entrega do pedido",
    )

    data_entrega_realizada = models.DateTimeField(
        verbose_name="Data de Entrega Realizada",
        null=True,
        blank=True,
        help_text="Data e hora em que o pedido foi efetivamente entregue",
    )

    observacoes = models.TextField(
        verbose_name="Observações",
        blank=True,
        help_text="Observações adicionais sobre o pedido",
    )

    created_at = models.DateTimeField(verbose_name="Criado em", auto_now_add=True)

    updated_at = models.DateTimeField(verbose_name="Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-data_pedido"]  # Mais recentes primeiro
        indexes = [
            models.Index(fields=["numero_pedido"]),
            models.Index(fields=["cliente", "status"]),
            models.Index(fields=["data_pedido"]),
            models.Index(fields=["status"]),
            models.Index(fields=["prioridade"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(valor_total__gte=0), name="valor_total_positivo"
            )
        ]

    def __str__(self):
        return f"Pedido {self.numero_pedido} - {self.cliente.name}"

    def clean(self):
        """
        Validações customizadas do modelo
        """
        super().clean()

        # Validar valor total
        if self.valor_total is not None and self.valor_total < 0:
            raise ValidationError(
                {"valor_total": "O valor total não pode ser negativo."}
            )

        # Validar data de entrega prevista
        if self.data_entrega_prevista:
            from django.utils import timezone

            if self.data_entrega_prevista < timezone.now().date():
                raise ValidationError(
                    {
                        "data_entrega_prevista": "A data de entrega prevista não pode ser no passado."
                    }
                )

        # Validar status e data de entrega
        if self.status == "entregue" and not self.data_entrega_realizada:
            raise ValidationError(
                {
                    "data_entrega_realizada": "Data de entrega realizada é obrigatória para pedidos entregues."
                }
            )

        # Validar descrição mínima
        if self.descricao and len(self.descricao.strip()) < 10:
            raise ValidationError(
                {"descricao": "Descrição deve ter pelo menos 10 caracteres."}
            )

    def save(self, *args, **kwargs):
        """
        Override do método save para gerar número do pedido e validações
        """
        # Gerar número do pedido se não existir
        if not self.numero_pedido:
            self.numero_pedido = self.generate_order_number()

        # Atualizar data de entrega realizada automaticamente
        if self.status == "entregue" and not self.data_entrega_realizada:
            from django.utils import timezone

            self.data_entrega_realizada = timezone.now()

        # Executar validações
        self.full_clean()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """
        Gera um número único para o pedido
        """
        import uuid
        from django.utils import timezone

        # Formato: PED-YYYYMM-XXXX (onde XXXX são os últimos 4 dígitos do UUID)
        now = timezone.now()
        year_month = now.strftime("%Y%m")
        unique_suffix = str(uuid.uuid4()).replace("-", "")[-4:].upper()

        return f"PED-{year_month}-{unique_suffix}"

    def get_absolute_url(self):
        """
        Retorna a URL para visualizar este pedido
        """
        return reverse("detail_pedido", kwargs={"id": self.pk})

    @property
    def is_overdue(self):
        """
        Verifica se o pedido está atrasado
        """
        if not self.data_entrega_prevista or self.status in ["entregue", "cancelado"]:
            return False

        from django.utils import timezone

        return timezone.now().date() > self.data_entrega_prevista

    @property
    def days_until_delivery(self):
        """
        Retorna quantos dias faltam para a entrega prevista
        """
        if not self.data_entrega_prevista or self.status in ["entregue", "cancelado"]:
            return None

        from django.utils import timezone

        delta = self.data_entrega_prevista - timezone.now().date()
        return delta.days

    @property
    def status_display_class(self):
        """
        Retorna classe CSS baseada no status para estilização
        """
        status_classes = {
            "pendente": "warning",
            "processando": "info",
            "enviado": "primary",
            "entregue": "success",
            "cancelado": "danger",
        }
        return status_classes.get(self.status, "secondary")

    @property
    def prioridade_display_class(self):
        """
        Retorna classe CSS baseada na prioridade para estilização
        """
        prioridade_classes = {
            "baixa": "success",
            "media": "warning",
            "alta": "danger",
            "urgente": "dark",
        }
        return prioridade_classes.get(self.prioridade, "secondary")

    def can_be_cancelled(self):
        """
        Verifica se o pedido pode ser cancelado
        """
        return self.status in ["pendente", "processando"]

    def cancel_order(self, reason=""):
        """
        Cancela o pedido
        """
        if not self.can_be_cancelled():
            raise ValidationError("Este pedido não pode ser cancelado.")

        self.status = "cancelado"
        if reason:
            self.observacoes = (
                f"{self.observacoes}\n\nMotivo do cancelamento: {reason}".strip()
            )
        self.save()

    @classmethod
    def get_status_statistics(cls):
        """
        Retorna estatísticas por status
        """
        from django.db.models import Count

        stats = (
            cls.objects.values("status").annotate(count=Count("id")).order_by("status")
        )

        return {item["status"]: item["count"] for item in stats}

    @classmethod
    def get_revenue_statistics(cls):
        """
        Retorna estatísticas de receita
        """
        from django.db.models import Sum, Avg, Count
        from django.utils import timezone

        # Estatísticas gerais
        total_stats = cls.objects.exclude(status="cancelado").aggregate(
            total_orders=Count("id"),
            total_revenue=Sum("valor_total"),
            average_order_value=Avg("valor_total"),
        )

        # Estatísticas do mês atual
        current_month = timezone.now().replace(day=1)
        monthly_stats = (
            cls.objects.filter(data_pedido__gte=current_month)
            .exclude(status="cancelado")
            .aggregate(monthly_orders=Count("id"), monthly_revenue=Sum("valor_total"))
        )

        return {
            "total_orders": total_stats["total_orders"] or 0,
            "total_revenue": total_stats["total_revenue"] or Decimal("0.00"),
            "average_order_value": total_stats["average_order_value"]
            or Decimal("0.00"),
            "monthly_orders": monthly_stats["monthly_orders"] or 0,
            "monthly_revenue": monthly_stats["monthly_revenue"] or Decimal("0.00"),
        }
