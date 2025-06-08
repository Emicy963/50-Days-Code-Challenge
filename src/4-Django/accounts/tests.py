from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages

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

    def test_register_view_get(self):
        """Testa se a página de registro é exibida corretamente"""
        response = self.client.get(reverse('register'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'register.html')

    def test_register_view_post_success(self):
        """Testa registro bem-sucedido de usuário"""
        data = {
            'name': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(reverse('register'), data)
        
        # Verifica redirecionamento
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('clients'))
        
        # Verifica se usuário foi criado
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Verifica mensagem de sucesso
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Conta criada com sucesso!")
