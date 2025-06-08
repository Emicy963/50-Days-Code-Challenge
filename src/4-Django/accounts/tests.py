from django.test import TestCase, Client
from django.contrib.auth.models import User

# TESTES PARA VIEWS TRADICIONAIS (TEMPLATES)

class AuthViewsTestCase(TestCase):
    """Testes para views de autenticação tradicionais"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.client = Client()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        self.user = User.objects.create_user(**self.user_data)
