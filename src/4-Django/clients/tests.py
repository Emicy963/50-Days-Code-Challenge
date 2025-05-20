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
    
    def test_create_valid_client(self):
        """
        Testar a criação de um cliente válido.
        """
        client = Client.objects.create(
            name='Maria Joana',
            email='maria@example.com',
            age=30
        )
        client.full_clean() # Não deve retornar nenhum erro
        client.save()

        # Verificar se foi salvo corretamente
        self.assertEqual(Client.objects.count(), 2)
        self.assertEqual(Client.objects.get(email='maria@example.com').name, 'Maria Joana')
