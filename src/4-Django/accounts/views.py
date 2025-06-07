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

        if User.objects.filter(email=email).exists():  # erificar se o email já existe
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
