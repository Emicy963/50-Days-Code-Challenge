from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Client


class ClientModelTest(TestCase):
    def setUp(self):
        """
        Configurações iniciais para testar o Client
        Criando alguns clientes para testar
        """
        # Cliente válido idade > 18
        self.validation_client = Client.objects.create(
            name="João Silva", email="joao@exemple.com", age=25
        )

    def test_create_valid_client(self):
        """
        Testar a criação de um cliente válido.
        """
        client = Client.objects.create(
            name="Maria Joana", email="maria@example.com", age=30
        )
        client.full_clean()  # Não deve retornar nenhum erro
        client.save()

        # Verificar se foi salvo corretamente
        self.assertEqual(Client.objects.count(), 2)
        self.assertEqual(
            Client.objects.get(email="maria@example.com").name, "Maria Joana"
        )

    def test_underage_client(self):
        """
        Testa a validzção da idade mínima.
        """
        underage_client = Client.objects.create(
            name="Constantino da Silva", email="constantino@example.com", age=16
        )

        # Verificar se a validação da idade está funcionando
        with self.assertRaises(ValidationError):
            underage_client.full_clean()
            underage_client.save()

    def test_validation_age_method(self):
        """
        Testa o método validation_age de forma individual.
        """
        client = Client(name="Test", email="test@example.com", age=16)

        with self.assertRaises(ValidationError):
            client.validation_age()

        # Alterar para idade válida
        client.age = 18
        try:
            client.validation_age()  # Não deve lançar excessões
            passed = True
        except ValidationError:
            passed = False

        self.assertTrue(passed)

    def test_str_method(self):
        """
        Testa o método __str__ do models
        """
        self.assertEqual(str(self.validation_client), "Client: João Silva")

    def test_clean_method(self):
        """
        Testa o método clean por completo
        """
        client = Client(name="Test", email="test@example.com", age=16)

        with self.assertRaises(ValidationError):
            client.clean()

        # Corrigir a idade e testar novamente
        client.age = 18
        try:
            client.clean()  # Deve funcionar sem erros
            passed = True
        except ValidationError:
            passed = False

        self.assertTrue(passed)

    def test_save_method_with_validation(self):
        """
        Testa se o método save da model esta a fazer a validação corretamente.
        """
        underage_client = Client(name="Lucas Mendes", email="lucas@example.com", age=14)

        with self.assertRaises(ValidationError):
            underage_client.save()  # Deve falhar devido a validação

        # Verificar se o cliente não foi salvo
        self.assertEqual(Client.objects.filter(email="lucas@example.com").count(), 0)
