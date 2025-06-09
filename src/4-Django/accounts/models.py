from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os


def user_profile_image_path(instance, filename):
    """
    Função para definir o caminho onde a imagem será salva
    """
    # Obter a extensão do arquivo
    ext = filename.split(".")[-1]

    # Criar nome único baseado no ID do usuário e timestamp
    filename = (
        f'user_{instance.user.id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.{ext}'
    )

    # Retornar o caminho completo
    return os.path.join("profile_images/", filename)


class UserProfile(models.Model):
    """
    Modelo para perfil estendido do usuário
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    profile_image = models.ImageField(
        upload_to=user_profile_image_path,
        null=True,
        blank=True,
        help_text="Foto de perfil do usuário",
    )

    bio = models.TextField(
        max_length=500, blank=True, null=True, help_text="Biografia do usuário"
    )

    phone = models.CharField(
        max_length=15, blank=True, null=True, help_text="Telefone do usuário"
    )

    birth_date = models.DateField(null=True, blank=True, help_text="Data de nascimento")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil do Usuário"
        verbose_name_plural = "Perfis dos Usuários"

    def __str__(self):
        return f"Perfil de {self.user.username}"

    @property
    def profile_image_url(self):
        """
        Retorna a URL da imagem de perfil ou None se não existir
        """
        if self.profile_image and hasattr(self.profile_image, "url"):
            return self.profile_image.url
        return None

    def delete_old_image(self):
        """
        Remove a imagem antiga quando uma nova é uploadada
        """
        if self.profile_image:
            try:
                if os.path.isfile(self.profile_image.path):
                    os.remove(self.profile_image.path)
            except Exception:
                pass


# Signal para criar perfil automaticamente quando um usuário é criado
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Cria um perfil automaticamente quando um usuário é criado
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Salva o perfil do usuário quando o usuário é salvo
    """
    if hasattr(instance, "profile"):
        instance.profile.save()


@receiver(pre_save, sender=UserProfile)
def delete_old_profile_image(sender, instance, **kwargs):
    """
    Remove a imagem antiga antes de salvar uma nova
    """
    if instance.pk:
        try:
            old_instance = UserProfile.objects.get(pk=instance.pk)
            if (
                old_instance.profile_image
                and old_instance.profile_image != instance.profile_image
            ):
                old_instance.delete_old_image()
        except UserProfile.DoesNotExist:
            pass
