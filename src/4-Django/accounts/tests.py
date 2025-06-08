from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.contrib.messages import get_messages
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APITestCase, APIClient

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

    def test_register_view_email_already_exists(self):
        """Testa registro com email já existente"""
        data = {
            'name': 'newuser',
            'email': 'test@example.com',  # Email já existe
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(reverse('register'), data)
        
        self.assertRedirects(response, reverse('register'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Este email já foi cadastrado", str(messages[0]))

    def test_register_view_username_already_exists(self):
        """Testa registro com nome de usuário já existente"""
        data = {
            'name': 'testuser',  # Username já existe
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }
        
        response = self.client.post(reverse('register'), data)
        
        self.assertRedirects(response, reverse('register'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Este nome de usuário já foi cadastrado", str(messages[0]))

    def test_register_view_passwords_dont_match(self):
        """Testa registro com senhas diferentes"""
        data = {
            'name': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'differentpassword'
        }
        
        response = self.client.post(reverse('register'), data)
        
        self.assertRedirects(response, reverse('register'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("As passwords são diferentes", str(messages[0]))

    def test_register_view_password_too_short(self):
        """Testa registro com senha muito curta"""
        data = {
            'name': 'newuser',
            'email': 'newuser@example.com',
            'password': '123',  # Menos de 8 caracteres
            'confirm_password': '123'
        }
        
        response = self.client.post(reverse('register'), data)
        
        self.assertRedirects(response, reverse('register'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("A password deve ter pelo menos 8 caracteres", str(messages[0]))

    def test_login_view_get(self):
        """Testa se a página de login é exibida corretamente"""
        response = self.client.get(reverse('login'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'login.html')


    def test_login_view_post_success(self):
        """Testa login bem-sucedido"""
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        
        response = self.client.post(reverse('login'), data)
        
        self.assertRedirects(response, reverse('clients'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Login realizado com sucesso!")

    def test_login_view_invalid_credentials(self):
        """Testa login com credenciais inválidas"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(reverse('login'), data)
        
        self.assertRedirects(response, reverse('login'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Usuário ou senha inválida", str(messages[0]))

    def test_login_view_empty_fields(self):
        """Testa login com campos vazios"""
        data = {
            'username': '',
            'password': ''
        }
        
        response = self.client.post(reverse('login'), data)
        
        self.assertRedirects(response, reverse('login'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Por favor, preencha todos os campos", str(messages[0]))

    def test_logout_view(self):
        """Testa logout do usuário"""
        # Primeiro faz login
        self.client.login(username='testuser', password='testpassword123')
        
        response = self.client.get(reverse('logout'))
        
        self.assertRedirects(response, reverse('login'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Logout realizado com sucesso!")


# TESTES PARA API VIEWS

class APIAuthTestCase(APITestCase):
    """Testes para views de API de autenticação"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create_user(**self.user_data)
        
        # Criar grupos de teste
        self.admin_group = Group.objects.create(name='Administradores')
        self.manager_group = Group.objects.create(name='Gerentes')
        self.employee_group = Group.objects.create(name='Funcionários')


    def get_jwt_token(self, user=None):
        """Gera token JWT para testes"""
        if user is None:
            user = self.user
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }
    
    def test_custom_token_obtain_pair_success(self):
        """Testa obtenção de token JWT com sucesso"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['message'], "Login realizado com sucesso")
        self.assertIn('expires_in', response.data)
    
    def test_custom_token_obtain_pair_invalid_credentials(self):
        """Testa obtenção de token com credenciais inválidas"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_custom_token_refresh_success(self):
        """Testa refresh de token JWT com sucesso"""
        tokens = self.get_jwt_token()
        url = reverse('token_refresh')
        data = {'refresh': tokens['refresh']}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['message'], "Token atualizado com sucesso")
    
    def test_custom_token_refresh_invalid_token(self):
        """Testa refresh com token inválido"""
        url = reverse('token_refresh')
        data = {'refresh': 'invalid_token'}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_view_success(self):
        """Testa registro via API com sucesso"""
        url = reverse('api_register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], "Usuário registrado com sucesso")
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        
        # Verifica se usuário foi criado
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_register_view_invalid_data(self):
        """Testa registro com dados inválidos"""
        url = reverse('api_register')
        data = {
            'username': '',  # Username vazio
            'email': 'invalid_email',  # Email inválido
            'password': '123',  # Senha muito curta
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_profile_view_get(self):
        """Testa obtenção do perfil do usuário"""
        tokens = self.get_jwt_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        url = reverse('user_profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
    
    def test_user_profile_view_patch(self):
        """Testa atualização do perfil do usuário"""
        tokens = self.get_jwt_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        url = reverse('user_profile')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Perfil atualizado com sucesso")
        
        # Verifica se foi atualizado no banco
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')

    def test_change_password_view_success(self):
        """Testa mudança de senha com sucesso"""
        tokens = self.get_jwt_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        url = reverse('change_password')
        data = {
            'old_password': 'testpassword123',
            'new_password': 'newpassword456',
            'new_password_confirm': 'newpassword456'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Senha alterada com sucesso")
    
    def test_change_password_view_wrong_old_password(self):
        """Testa mudança de senha com senha antiga incorreta"""
        tokens = self.get_jwt_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        
        url = reverse('change_password')
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpassword456',
            'new_password_confirm': 'newpassword456'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('django.core.mail.send_mail')
    def test_password_reset_view_success(self, mock_send_mail):
        """Testa solicitação de reset de senha com sucesso"""
        mock_send_mail.return_value = True
        
        url = reverse('password_reset')
        data = {'email': 'test@example.com'}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Email de reset enviado com sucesso")
        mock_send_mail.assert_called_once()
    
    def test_password_reset_view_invalid_email(self):
        """Testa reset de senha com email inválido"""
        url = reverse('password_reset')
        data = {'email': 'nonexistent@example.com'}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
