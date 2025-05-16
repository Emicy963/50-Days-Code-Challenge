def custom_split(text:str, delimiter=" ")->list:
    """
    Função que simula o comportamento da função split() nativa do Python
    
    Args:
        text (str): A string que será dividida
        delimiter (str, opcional): O delimitador usado para separar a string. Padrão é espaço.
        
    Returns:
        list: Uma lista contendo as substrings separadas pelo delimitador
    """
    # Verificar se os argumentos são validos
    if not isinstance(text, str):
        raise TypeError("O texto deve ser uma string")
    if not isinstance(delimiter, str):
        raise TypeError("O delimitador deve ser uma string")
    
    result = [] # Lista para armazenar as substrings
    current_word = "" # String temporária para construir cada substring

    # Caso especial: se o delimitador for uma string vazia, cada caracter vira um item na lista
    if delimiter=="":
        for char in text:
            result.append(char)
        return result
    
    # Percorrer cada caractere da string
    i = 0
    while i<len(text):
        # Verificar se encontramos o delimitador
        if text[i:i+len(delimiter)]==delimiter:
            # Adicionar a palavra atual à lista de resultados
            result.append(current_word)
            current_word= "" # Reiniciar a palavra atual
            i += len(delimiter) # Avançar o índice para depois do delimitador
        else:
            # Adicionar o caractere atual à palavra atual
            current_word += text[i]
            i += 1
    
    # Adicionar a última palavra à lista de resultados (caso a string não termine com o delimitador)
    result.append(current_word)

    return result
