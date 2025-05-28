# 🔐 Sistema de Permissões por Grupo - Guia de Implementação

## 📋 Visão Geral

Este sistema implementa três níveis de permissão para o CRUD de clientes:

- **👑 Administradores**: Acesso completo (criar, editar, deletar, gerenciar usuários)
- **⚡ Gerentes**: Criar e editar clientes (não podem deletar)
- **👤 Funcionários**: Apenas visualizar clientes

## 🚀 Passos para Implementação

### 1. Atualizar o arquivo de views

Substitua o conteúdo do seu arquivo `clientes/views.py` pelo código fornecido no primeiro artefato. As principais mudanças são:

- Decorator personalizado `@group_required()` para verificar grupos
- Verificação de permissões em cada view
- Passagem de variáveis de controle para os templates
- Nova view `manage_users()` para administradores

### 2. Criar o comando de gerenciamento

Crie a estrutura de pastas e arquivo:

```
clientes/
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── setup_groups.py
```

Cole o código do segundo artefato em `setup_groups.py`.

### 3. Executar o comando para criar grupos

```bash
python manage.py setup_groups
```

Este comando criará os três grupos e suas respectivas permissões.

### 4. Atualizar os templates

- Substitua `templates/clients.html` pelo terceiro artefato
- Crie `templates/manage_users.html` com o conteúdo do quarto artefato

### 5. Atualizar as URLs

Adicione a nova URL para gerenciamento de usuários no seu `clientes/urls.py`:

```python
path('manage-users/', views.manage_users, name='manage_users'),
```

### 6. Aplicar migrações

```bash
python manage.py makemigrations
python manage.py migrate
```

## 👥 Como Atribuir Usuários aos Grupos

### Opção 1: Via Django Admin

1. Acesse `/admin/`
2. Vá em "Users"
3. Selecione um usuário
4. Na seção "Permissions", adicione aos grupos desejados

### Opção 2: Via Interface Custom (Recomendado)

1. Faça login como administrador
2. Acesse a página de clientes
3. Clique em "Gerenciar Usuários"
4. Use os modais para editar os grupos de cada usuário

### Opção 3: Via Shell do Django

```python
python manage.py shell

from django.contrib.auth.models import User, Group

# Pegar um usuário
user = User.objects.get(username='nome_usuario')

# Pegar um grupo
group = Group.objects.get(name='Gerentes')

# Adicionar usuário ao grupo
user.groups.add(group)

# Ou limpar todos os grupos e adicionar novos
user.groups.clear()
user.groups.add(Group.objects.get(name='Funcionários'))
```

## 🔧 Funcionalidades Implementadas

### Sistema de Permissões

- **Decorators personalizados** para verificar grupos
- **Verificação condicional** de permissões nas views
- **Controle de exibição** de botões e ações nos templates

### Interface de Gerenciamento

- **Listagem de usuários** com seus grupos atuais
- **Edição de grupos** via modais Bootstrap
- **Informações visuais** sobre permissões de cada grupo

### Segurança

- **Proteção de rotas** com decorators
- **Verificação dupla** (decorator + template)
- **Mensagens de erro** para acesso negado

## 🎨 Personalizações Opcionais

### 1. Middleware de Auditoria

Para registrar quem fez qual ação:

```python
# middleware.py
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated and request.method == 'POST':
            logger.info(f"User {request.user.username} performed {request.method} on {request.path}")
```

### 2. Permissões mais Granulares

Você pode criar permissões específicas por campo:

```python
# models.py
class Client(models.Model):
    # ... campos existentes
    
    class Meta:
        permissions = [
            ("can_edit_client_email", "Can edit client email"),
            ("can_view_client_age", "Can view client age"),
        ]
```

### 3. Decorator para Permissões Django Nativas

```python
from django.contrib.auth.decorators import permission_required

@permission_required('clientes.add_client')
def create_client(request):
    # sua view
```

## 🐛 Troubleshooting

### Erro: "Group matching query does not exist"

Execute o comando de setup:

```bash
python manage.py setup_groups
```

### Usuário não consegue acessar nenhuma página

Verifique se o usuário está em pelo menos um grupo:

```python
user = User.objects.get(username='usuario')
print(user.groups.all())
```

### Botões não aparecem/desaparecem corretamente

Verifique se as variáveis de contexto estão sendo passadas nas views:

- `can_create`
- `can_edit`
- `can_delete`

## 📊 Testando o Sistema

### 1. Criar usuários de teste

```python
python manage.py shell

from django.contrib.auth.models import User, Group

# Criar usuários
admin_user = User.objects.create_user('admin_test', 'admin@test.com', 'senha123')
manager_user = User.objects.create_user('manager_test', 'manager@test.com', 'senha123')
employee_user = User.objects.create_user('employee_test', 'employee@test.com', 'senha123')

# Adicionar aos grupos
admin_user.groups.add(Group.objects.get(name='Administradores'))
manager_user.groups.add(Group.objects.get(name='Gerentes'))
employee_user.groups.add(Group.objects.get(name='Funcionários'))
```

### 2. Testar cada nível de acesso

- **Funcionário**: Deve apenas visualizar clientes
- **Gerente**: Pode criar e editar, mas não deletar
- **Administrador**: Acesso completo + gerenciamento de usuários

## ✅ Checklist de Implementação

- [ ] Código das views atualizado
- [ ] Comando `setup_groups.py` criado
- [ ] Comando executado (`python manage.py setup_groups`)
- [ ] Templates atualizados
- [ ] URLs adicionadas
- [ ] Usuários atribuídos aos grupos
- [ ] Testado com diferentes níveis de acesso
- [ ] Verificado que botões aparecem/desaparecem corretamente

## 🎉 Conclusão

Com esta implementação, você terá um sistema robusto de permissões que:

- ✅ Controla acesso por grupos de usuários
- ✅ Exibe interface adequada para cada nível
- ✅ Fornece ferramenta para gerenciar usuários
- ✅ Mantém segurança em todas as camadas
- ✅ É facilmente extensível para novas funcionalidades

O desafio 35 está completo! 🚀
