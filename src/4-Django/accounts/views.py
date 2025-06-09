from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages


def register_view(request):
    """
    Método para resgister um novo user no site
    """
    if request.method == "GET":
        return render(request, "register.html")
    elif request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if User.objects.filter(email=email).exists():  # Verificar se o email já existe
            messages.error(request, "Este email já foi cadastrado. Tente um diferente!")
            return redirect("register")
        if User.objects.filter(username=name).exists():
            messages.error(
                request, "Este nome de usuário já foi cadastrado. Tente um diferente!"
            )
            return redirect("register")

        if password != confirm_password:
            messages.error(request, "As passwords são diferentes!")
            return redirect("register")
        if len(password) < 8:
            messages.error(request, "A password deve ter pelo menos 8 caracteres!")
            return redirect("register")

        try:
            # Criar e autenticar o usuário
            user = User.objects.create_user(
                username=name, email=email, password=password
            )
            user = authenticate(request, username=name, password=password)
            if user is not None:
                login(request, user)  # Fazer login do usuário após o registro
                messages.success(request, "Conta criada com sucesso!")
                return redirect("clients")
            else:
                messages.error(request, "Erro ao autenticar usuário!")
                return redirect("register")
        except Exception as err:
            messages.error(request, f"Erro: {str(err)}")
            return redirect("register")


def login_view(request):
    """
    Método para fazer login no site
    """
    if request.method == "GET":
        return render(request, "login.html")
    elif request.method == "POST":
        """
        Método para fazer login no site
        """
        username = request.POST.get("username")
        password = request.POST.get("password")
        if not username or not password:
            messages.error(request, "Por favor, preencha todos os campos!")
            return redirect("login")
        try:
            # Verificar se o usuário existe e autenticar
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Login realizado com sucesso!")
                return redirect("clients")
            else:
                messages.error(request, "Usuário ou senha inválida!")
                return redirect("login")
        except Exception as err:
            messages.error(request, f"Erro: {str(err)}")
            return redirect("login")


def logout_view(request):
    """
    Método para fazer logout do site
    """
    logout(request)
    messages.success(request, "Logout realizado com sucesso!")
    return redirect("login")


# ==== Views para autenticação e gerenciamento de usuários ====
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import authenticate
from .models import UserProfile
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    PasswordResetSerializer,
    UserCompleteProfileSerializer,
    ProfileImageUploadSerializer,
)
import jwt


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    View customizada para obtenção de token JWT
    """

    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)

            if response.status_code == 200:
                # Log do login bem-sucedido
                user = authenticate(
                    username=request.data.get("username"),
                    password=request.data.get("password"),
                )
                if user:
                    user.last_login = timezone.now()
                    user.save(update_fields=["last_login"])

                # Adicionar informações extras na resposta
                response.data["message"] = "Login realizado com sucesso"
                response.data["expires_in"] = settings.SIMPLE_JWT[
                    "ACCESS_TOKEN_LIFETIME"
                ].total_seconds()

            return response

        except Exception as e:
            return Response(
                {"error": "Erro interno do servidor", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomTokenRefreshView(TokenRefreshView):
    """
    View customizada para refresh de token JWT
    """

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)

            if response.status_code == 200:
                response.data["message"] = "Token atualizado com sucesso"
                response.data["expires_in"] = settings.SIMPLE_JWT[
                    "ACCESS_TOKEN_LIFETIME"
                ].total_seconds()

            return response

        except TokenError as e:
            return Response(
                {"error": "Token inválido", "detail": str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class LogoutView(APIView):
    """
    View para logout (blacklist do refresh token)
    """

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")

            if not refresh_token:
                return Response(
                    {"error": "Refresh token é obrigatório"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Logout realizado com sucesso"}, status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": "Token inválido", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RegisterView(APIView):
    """
    View para registro de novos usuários
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # Gerar tokens para o usuário recém-criado
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "message": "Usuário registrado com sucesso",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserCompleteProfileView(APIView):
    """
    View para visualização e atualização completa do perfil do usuário
    """

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser]  # Para upload de arquivos

    def get(self, request):
        """
        Retorna perfil completo do usuário
        """
        serializer = UserCompleteProfileSerializer(
            request.user, context={"request": request}
        )
        return Response(serializer.data)

    def patch(self, request):
        """
        Atualiza dados básicos do usuário
        """
        user_data = {}
        profile_data = {}

        # Separar dados do User e UserProfile
        user_fields = ["first_name", "last_name", "email"]
        profile_fields = ["bio", "phone", "birth_date", "profile_image"]

        for key, value in request.data.items():
            if key in user_fields:
                user_data[key] = value
            elif key in profile_fields:
                profile_data[key] = value

        # Atualizar dados do usuário
        if user_data:
            user_serializer = UserCompleteProfileSerializer(
                request.user, data=user_data, partial=True, context={"request": request}
            )
            if user_serializer.is_valid():
                user_serializer.save()
            else:
                return Response(
                    user_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )

        # Atualizar perfil do usuário
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile_serializer = UserProfileSerializer(
                profile, data=profile_data, partial=True, context={"request": request}
            )
            if profile_serializer.is_valid():
                profile_serializer.save()
            else:
                return Response(
                    profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )

        # Retornar dados atualizados
        updated_serializer = UserCompleteProfileSerializer(
            request.user, context={"request": request}
        )

        return Response(
            {
                "message": "Perfil atualizado com sucesso",
                "user": updated_serializer.data,
            }
        )


class UserProfileView(APIView):
    """
    View para visualização e atualização do perfil do usuário (ATUALIZADA)
    """

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        # Usar o novo serializer completo
        serializer = UserCompleteProfileSerializer(
            request.user, context={"request": request}
        )
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserCompleteProfileSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Perfil atualizado com sucesso", "user": serializer.data}
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileImageUploadView(APIView):
    """
    View específica para upload de imagem de perfil
    """

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        """
        Upload de nova imagem de perfil
        """
        serializer = ProfileImageUploadSerializer(data=request.data)

        if serializer.is_valid():
            profile, created = UserProfile.objects.get_or_create(user=request.user)

            # Salvar nova imagem
            profile.profile_image = serializer.validated_data["profile_image"]
            profile.save()

            # Redimensionar imagem usando o método do serializer
            profile_serializer = UserProfileSerializer(
                profile, context={"request": request}
            )

            return Response(
                {
                    "message": "Imagem de perfil atualizada com sucesso",
                    "profile_image_url": profile_serializer.data["profile_image_url"],
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """
        Remove imagem de perfil
        """
        try:
            profile = request.user.profile
            if profile.profile_image:
                profile.delete_old_image()
                profile.profile_image = None
                profile.save()

                return Response({"message": "Imagem de perfil removida com sucesso"})
            else:
                return Response(
                    {"message": "Usuário não possui imagem de perfil"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Perfil não encontrado"}, status=status.HTTP_404_NOT_FOUND
            )


class UserProfileDetailView(APIView):
    """
    View para detalhes específicos do perfil
    """

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        """
        Retorna apenas dados do perfil estendido
        """
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, context={"request": request})
        return Response(serializer.data)

    def patch(self, request):
        """
        Atualiza apenas dados do perfil estendido
        """
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(
            profile, data=request.data, partial=True, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Perfil atualizado com sucesso", "profile": serializer.data}
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    View para mudança de senha
    """

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()

            return Response({"message": "Senha alterada com sucesso"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    """
    View para solicitação de reset de senha
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            user = User.objects.get(email=email)

            # Gerar token temporário
            reset_token = get_random_string(32)

            # Armazenar token temporariamente (em produção, use cache ou banco)
            # Aqui vamos usar um campo temporário no modelo User ou cache

            # Enviar email (configurar SMTP no settings)
            try:
                send_mail(
                    "Reset de Senha - Sistema de Clientes",
                    f"Use este token para resetar sua senha: {reset_token}",
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )

                return Response({"message": "Email de reset enviado com sucesso"})

            except Exception as e:
                return Response(
                    {"error": "Erro ao enviar email", "detail": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TokenVerifyView(APIView):
    """
    View para verificar se um token JWT é válido
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token")

        if not token:
            return Response(
                {"error": "Token é obrigatório"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Verificar se o token é válido
            from rest_framework_simplejwt.tokens import UntypedToken

            UntypedToken(token)

            # Decodificar o token para obter informações do usuário
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

            user_id = decoded_token.get("user_id")
            user = User.objects.get(id=user_id)

            return Response(
                {
                    "valid": True,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "groups": [group.name for group in user.groups.all()],
                    },
                    "expires_at": decoded_token.get("exp"),
                }
            )

        except jwt.ExpiredSignatureError:
            return Response(
                {"valid": False, "error": "Token expirado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        except (jwt.InvalidTokenError, User.DoesNotExist):
            return Response(
                {"valid": False, "error": "Token inválido"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def user_info(request):
    """
    Função para obter informações do usuário autenticado
    """
    user = request.user

    return Response(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "groups": [group.name for group in user.groups.all()],
            "permissions": get_user_permissions(user),
            "last_login": user.last_login,
            "date_joined": user.date_joined,
        }
    )


def get_user_permissions(user):
    """
    Função auxiliar para obter permissões do usuário
    """
    permissions = []

    if user.groups.filter(name="Administradores").exists():
        permissions = ["all"]
    elif user.groups.filter(name="Gerentes").exists():
        permissions = ["read", "write", "update", "delete_own"]
    elif user.groups.filter(name="Funcionários").exists():
        permissions = ["read", "update_status"]

    return permissions
