from django.test import TestCase

from .models import Client

class ClientModelTest(TestCase):
    def setUp(self):
        """
        Configurações iniciais para testar o Client
        Criando alguns clientes para testar
        """
        # Cliente válido idade > 18
        self.validation_client = Client.objects.create(
            name='João Silva',
            email='joao@exemple.com',
            age=25
        )
