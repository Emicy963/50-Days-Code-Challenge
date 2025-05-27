from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate, views
from django.contrib import messages

def resgister_view(request):
    """
    Método para resgister um novo user no site
    """
    if request.method=='GET':
        return render(request, 'register.html')
    elif request.method=='POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Este email já foi cadastrado. Tente um diferente!')
        
        if password!=confirm_password:
            messages.error(request, 'As passwords são diferentes!')
            return redirect('resgister')
        
        try:
            user = User.objects.create_user(
                username=name,
                email=email,
                password=password
            )
            user = authenticate(request, username=name, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Conta criada com sucesso!')
                return redirect('clients')
            else:
                messages.error(request, 'Erro ao autenticar usuário!')
                return redirect('register')
        except Exception as err:
            messages.error(request, f'Erro: {str(err)}')
            return redirect('register')

def login_view(request):
    """
    Método para fazer login no site
    """
    if request.method=='GET':
        return render(request, 'login.html')
    elif request.method=='POST':
        """
        Método para fazer login no site
        """
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Login realizado com sucesso!')
                return redirect('clients')
            else:
                messages.error(request, 'Usuário ou senha inválida!')
                return redirect('login')
        except Exception as err:
            messages.error(request, f'Erro: {str(err)}')
            return redirect('login')
