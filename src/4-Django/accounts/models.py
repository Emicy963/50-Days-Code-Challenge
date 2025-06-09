from django.db import models
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
