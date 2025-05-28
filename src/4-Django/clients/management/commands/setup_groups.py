from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from clients.models import Client

class Command(BaseCommand):
    help = 'Configura grupos de usuários e suas permissões'

    def handle(self, *args, **options):
        # Criar os grupos
        administradores, created = Group.objects.get_or_create(name='Administradores')
        gerentes, created = Group.objects.get_or_create(name='Gerentes')
        funcionarios, created = Group.objects.get_or_create(name='Funcionários')

        # Obter o content type do modelo Client
        client_content_type = ContentType.objects.get_for_model(Client)

        # Criar permissões customizadas se não existirem
        view_client_perm, created = Permission.objects.get_or_create(
            codename='view_client',
            name='Can view client',
            content_type=client_content_type,
        )
        
        add_client_perm, created = Permission.objects.get_or_create(
            codename='add_client',
            name='Can add client',
            content_type=client_content_type,
        )
        
        change_client_perm, created = Permission.objects.get_or_create(
            codename='change_client',
            name='Can change client',
            content_type=client_content_type,
        )
        
        delete_client_perm, created = Permission.objects.get_or_create(
            codename='delete_client',
            name='Can delete client',
            content_type=client_content_type,
        )

        # Configurar permissões para cada grupo
        
        # Administradores - Todas as permissões
        administradores.permissions.set([
            view_client_perm,
            add_client_perm,
            change_client_perm,
            delete_client_perm,
        ])

        # Gerentes - Visualizar, criar e editar (sem deletar)
        gerentes.permissions.set([
            view_client_perm,
            add_client_perm,
            change_client_perm,
        ])

        # Funcionários - Apenas visualizar
        funcionarios.permissions.set([
            view_client_perm,
        ])

        self.stdout.write(
            self.style.SUCCESS('Grupos e permissões configurados com sucesso!')
        )
        
        self.stdout.write('Grupos criados:')
        self.stdout.write(f'- Administradores: {list(administradores.permissions.values_list("name", flat=True))}')
        self.stdout.write(f'- Gerentes: {list(gerentes.permissions.values_list("name", flat=True))}')
        self.stdout.write(f'- Funcionários: {list(funcionarios.permissions.values_list("name", flat=True))}')
        
        self.stdout.write('\nPara atribuir usuários aos grupos, use o admin Django ou a view manage_users.')
