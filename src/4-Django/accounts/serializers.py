from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import UserProfile
from PIL import Image
import io
from django.core.files.uploadedfile import InMemoryUploadedFile


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer customizado para JWT token com informações adicionais do usuário
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Adicionar claims customizados
        token["username"] = user.username
        token["email"] = user.email
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["is_staff"] = user.is_staff
        token["is_superuser"] = user.is_superuser

        # Adicionar grupos do usuário
        token["groups"] = [group.name for group in user.groups.all()]

        # Adicionar permissões específicas
        permissions = []
        if user.groups.filter(name="Administradores").exists():
            permissions = ["all"]
        elif user.groups.filter(name="Gerentes").exists():
            permissions = ["read", "write", "update"]
        elif user.groups.filter(name="Funcionários").exists():
            permissions = ["read", "update_status"]

        token["permissions"] = permissions

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Adicionar informações do usuário na resposta
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "is_staff": self.user.is_staff,
            "groups": [group.name for group in self.user.groups.all()],
            "last_login": self.user.last_login,
            "profile_image": (
                self.user.profile.profile_image_url
                if hasattr(self.user, "profile")
                else None
            ),
        }

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para perfil estendido do usuário
    """

    profile_image = serializers.ImageField(required=False, allow_null=True)
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "profile_image",
            "profile_image_url",
            "bio",
            "phone",
            "birth_date",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "profile_image_url"]

    def get_profile_image_url(self, obj):
        """
        Retorna a URL completa da imagem de perfil
        """
        if obj.profile_image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None

    def validate_profile_image(self, value):
        """
        Valida a imagem de perfil
        """
        if value:
            # Verificar tamanho do arquivo (máximo 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(
                    "A imagem não pode ser maior que 5MB."
                )

            # Verificar formato do arquivo
            allowed_formats = ["JPEG", "PNG", "GIF", "WEBP"]
            try:
                img = Image.open(value)
                if img.format not in allowed_formats:
                    raise serializers.ValidationError(
                        f"Formato não suportado. Use: {', '.join(allowed_formats)}"
                    )
            except Exception:
                raise serializers.ValidationError("Arquivo de imagem inválido.")

        return value

    def update(self, instance, validated_data):
        """
        Atualiza o perfil e redimensiona a imagem se necessário
        """
        profile_image = validated_data.get("profile_image")

        if profile_image:
            # Redimensionar imagem se necessário
            validated_data["profile_image"] = self.resize_image(profile_image)

        return super().update(instance, validated_data)

    def resize_image(self, image):
        """
        Redimensiona a imagem para um tamanho padrão
        """
        img = Image.open(image)

        # Definir tamanho máximo
        max_size = (800, 800)

        # Manter proporção
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Converter para RGB se necessário
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Salvar em buffer
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)

        # Criar novo arquivo
        return InMemoryUploadedFile(
            buffer,
            "ImageField",
            f"{image.name.split('.')[0]}.jpg",
            "image/jpeg",
            buffer.tell(),
            None,
        )


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de novos usuários
    """

    password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )
    password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "As senhas não coincidem."}
            )
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email já está em uso.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nome de usuário já está em uso.")
        return value

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Adicionar ao grupo padrão (Funcionários)
        from django.contrib.auth.models import Group

        funcionarios_group, created = Group.objects.get_or_create(name="Funcionários")
        user.groups.add(funcionarios_group)

        return user


class UserCompleteProfileSerializer(serializers.ModelSerializer):
    """
    Serializer completo para perfil do usuário (User + UserProfile)
    """

    profile = UserProfileSerializer(read_only=True)
    groups = serializers.StringRelatedField(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "is_active",
            "date_joined",
            "last_login",
            "groups",
            "profile",
            "profile_image_url",
        ]
        read_only_fields = ["username", "date_joined", "last_login"]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_profile_image_url(self, obj):
        """
        Retorna a URL da imagem de perfil
        """
        if hasattr(obj, "profile") and obj.profile.profile_image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.profile.profile_image.url)
            return obj.profile.profile_image.url
        return None


class ProfileImageUploadSerializer(serializers.Serializer):
    """
    Serializer específico para upload de imagem de perfil
    """

    profile_image = serializers.ImageField()

    def validate_profile_image(self, value):
        """
        Valida a imagem de perfil
        """
        # Verificar tamanho do arquivo (máximo 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("A imagem não pode ser maior que 5MB.")

        # Verificar formato do arquivo
        allowed_formats = ["JPEG", "PNG", "GIF", "WEBP"]
        try:
            img = Image.open(value)
            if img.format not in allowed_formats:
                raise serializers.ValidationError(
                    f"Formato não suportado. Use: {', '.join(allowed_formats)}"
                )
        except Exception:
            raise serializers.ValidationError("Arquivo de imagem inválido.")

        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para mudança de senha
    """

    old_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )
    new_password_confirm = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "As senhas não coincidem."}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Senha atual incorreta.")
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer para reset de senha
    """

    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Usuário com este email não encontrado.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer para confirmação de reset de senha
    """

    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(style={"input_type": "password"})

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "As senhas não coincidem."}
            )
        return attrs
