from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from clients.models import Client


class Command(BaseCommand):
    help = "Configura grupos de usuários e suas permissões"

    def handle(self, *args, **options):
        # Criar os grupos
        administradores, created = Group.objects.get_or_create(name="Administradores")
        if created:
            self.stdout.write(self.style.SUCCESS('Grupo "Administradores" criado'))
        else:
            self.stdout.write(self.style.WARNING('Grupo "Administradores" já existe'))

        gerentes, created = Group.objects.get_or_create(name="Gerentes")
        if created:
            self.stdout.write(self.style.SUCCESS('Grupo "Gerentes" criado'))
        else:
            self.stdout.write(self.style.WARNING('Grupo "Gerentes" já existe'))

        funcionarios, created = Group.objects.get_or_create(name="Funcionários")
        if created:
            self.stdout.write(self.style.SUCCESS('Grupo "Funcionários" criado'))
        else:
            self.stdout.write(self.style.WARNING('Grupo "Funcionários" já existe'))

        # Obter o content type do modelo Client
        client_content_type = ContentType.objects.get_for_model(Client)

        # Buscar permissões existentes (criadas automaticamente pelo Django)
        try:
            view_client_perm = Permission.objects.get(
                codename="view_client",
                content_type=client_content_type,
            )
            self.stdout.write('Permissão "view_client" encontrada')
        except Permission.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    'Permissão "view_client" não encontrada. Execute as migrações primeiro.'
                )
            )
            return

        try:
            add_client_perm = Permission.objects.get(
                codename="add_client",
                content_type=client_content_type,
            )
            self.stdout.write('Permissão "add_client" encontrada')
        except Permission.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    'Permissão "add_client" não encontrada. Execute as migrações primeiro.'
                )
            )
            return

        try:
            change_client_perm = Permission.objects.get(
                codename="change_client",
                content_type=client_content_type,
            )
            self.stdout.write('Permissão "change_client" encontrada')
        except Permission.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    'Permissão "change_client" não encontrada. Execute as migrações primeiro.'
                )
            )
            return

        try:
            delete_client_perm = Permission.objects.get(
                codename="delete_client",
                content_type=client_content_type,
            )
            self.stdout.write('Permissão "delete_client" encontrada')
        except Permission.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    'Permissão "delete_client" não encontrada. Execute as migrações primeiro.'
                )
            )
            return

        # Configurar permissões para cada grupo

        # Administradores - Todas as permissões
        administradores.permissions.set(
            [
                view_client_perm,
                add_client_perm,
                change_client_perm,
                delete_client_perm,
            ]
        )

        # Gerentes - Visualizar, criar e editar (sem deletar)
        gerentes.permissions.set(
            [
                view_client_perm,
                add_client_perm,
                change_client_perm,
            ]
        )

        # Funcionários - Apenas visualizar
        funcionarios.permissions.set(
            [
                view_client_perm,
            ]
        )

        self.stdout.write(
            self.style.SUCCESS("Grupos e permissões configurados com sucesso!")
        )

        self.stdout.write("\nGrupos criados:")
        self.stdout.write(
            f'- Administradores: {list(administradores.permissions.values_list("name", flat=True))}'
        )
        self.stdout.write(
            f'- Gerentes: {list(gerentes.permissions.values_list("name", flat=True))}'
        )
        self.stdout.write(
            f'- Funcionários: {list(funcionarios.permissions.values_list("name", flat=True))}'
        )

        self.stdout.write(
            "\nPara atribuir usuários aos grupos, use o admin Django ou a view manage_users."
        )
