from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import os

def user_profile_photo_path(instance, filename):
    """
    Funcão para definir o caminho do arquivo de foto de perfil do usuário.
    """
    # Obter extensão do arquivo
    ext = filename.split('.')[-1]
    # Criar nome único baseado no ID do usuário
    filename = f"user_{instance.user.id}_profile.{ext}"
    return os.path.join('profile_photos', filename)

class UserProfile(models.Model):
    """
    Modelo para perfil estendido do usuário
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_photo = models.ImageField(
        upload_to=user_profile_photo_path,
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])
        ],
        help_text="Formatos aceitos: JPG, JPEG, PNG, GIF. Tamanho máximo: 2MB"
    )
    bio = models.TextField(max_length=500, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
