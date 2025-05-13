def login(users: dict, username_or_email: str, password: str) -> str:
    """
    Realiza o login do usuário verificando as credenciais fornecidas.

    Args:
        users: Dicionário contendo informações dos usuários (username, email, password)
        username_or_email: Nome de usuário ou email fornecido
        password: Senha fornecida pelo usuário

    Returns:
        Mensagem de sucesso quando o login é realizado corretamente

    Raises:
        Exception: Quando as credenciais são inválidas ou informações estão faltando
    """
    # Verificar se as credência foram digitadas
    if not username_or_email:
        raise Exception("Username ou email é obrigatório!")
    
    if not password:
        raise Exception("Senha é obrigatória.")
    
    # Verificando se o input é um email ou username
    is_email = '@' in username_or_email # Verificando a presença do @ para identificar se é email

    # Buscando o indíce do usuário pelo email ou username
    user_index = -1

    if is_email:
        # Tentativa de busca pelo email
        if username_or_email in users["email"]:
            user_index = users["email"].index(username_or_email)
    else:
        if username_or_email in users["username"]:
            user_index = users["username"].index(username_or_email)
    
    # Verifica se encontrou o usuário e se password corresponde
    if user_index >= 0 and users["password"][user_index] == password:
        return "Login feito com sucesso!"
    else:
        raise Exception("Username/email ou senha incorretos.")
