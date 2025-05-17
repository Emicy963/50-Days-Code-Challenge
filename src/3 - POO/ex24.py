class JSONSerializer:
    """
    Classe responsável por serializar objetos Python para o formato JSON.
    Converte tipos nativos do Python (dict, list, str, int, float, bool, None) 
    para suas representações em string no formato JSON.
    """ 
    def serialize(self, obj):
        """
        Método principal que converte um objeto Python para string JSON.
        
        Args:
            obj: Objeto Python a ser serializado
            
        Returns:
            String no formato JSON representando o objeto
            
        Raises:
            TypeError: Se o objeto não for serializável
        """
        if obj is None:
            return "null"  # Valor nulo em JSON
        elif isinstance(obj, bool):
            return "true" if obj else "false"  # Booleanos em JSON são lowercase
        elif isinstance(obj, (int, float)):
            return str(obj)  # Números são representados diretamente
        elif isinstance(obj, str):
            return self._serialize_string(obj)  # Strings precisam de aspas e escaping
        elif isinstance(obj, list):
            return self._serialize_list(obj)  # Listas viram arrays JSON
        elif isinstance(obj, dict):
            return self._serialize_dict(obj)  # Dicionários viram objetos JSON
        else:
            raise TypeError(f"Objeto do tipo {type(obj)} não é serializável para JSON")
    
    def _serialize_string(self, s):
        """
        Serializa uma string para o formato JSON com aspas duplas e
        caracteres especiais escapados conforme a especificação JSON.
        
        Args:
            s: String a ser serializada
            
        Returns:
            String formatada conforme padrão JSON
        """
        # Mapeamento de caracteres que precisam ser escapados em JSON
        escape_chars = {
            '"': '\\"',    # Aspas duplas
            '\\': '\\\\',  # Barra invertida
            '\b': '\\b',   # Backspace
            '\f': '\\f',   # Form feed
            '\n': '\\n',   # Nova linha
            '\r': '\\r',   # Retorno de carro
            '\t': '\\t'    # Tabulação
        }
        
        result = '"'  # Abre aspas
        for char in s:
            # Substitui caracteres especiais ou mantém o original
            result += escape_chars.get(char, char)
        result += '"'  # Fecha aspas
        return result
    
    def _serialize_list(self, lst):
        """
        Serializa uma lista Python para um array JSON.
        
        Args:
            lst: Lista Python a ser serializada
            
        Returns:
            String representando um array JSON
        """
        if not lst:
            return "[]"  # Lista vazia
            
        result = "["  # Abre colchete
        for i, item in enumerate(lst):
            if i > 0:
                result += ", "  # Adiciona vírgula entre elementos
            result += self.serialize(item)  # Serializa cada item recursivamente
        result += "]"  # Fecha colchete
        return result
    
    def _serialize_dict(self, d):
        """
        Serializa um dicionário Python para um objeto JSON.
        
        Args:
            d: Dicionário Python a ser serializado
            
        Returns:
            String representando um objeto JSON
        """
        if not d:
            return "{}"  # Dicionário vazio
            
        result = "{"  # Abre chave
        for i, (key, value) in enumerate(d.items()):
            if i > 0:
                result += ", "  # Adiciona vírgula entre pares chave-valor
            # Em JSON, as chaves devem ser strings
            result += f"{self._serialize_string(str(key))}: {self.serialize(value)}"
        result += "}"  # Fecha chave
        return result


def to_json(obj):
    """
    Função auxiliar para facilitar a serialização de objetos Python para JSON.
    
    Args:
        obj: Objeto Python a ser convertido para JSON
        
    Returns:
        String no formato JSON
        
    Examples:
        >>> to_json({"nome": "Ana", "idade": 30})
        '{"nome": "Ana", "idade": 30}'
        >>> to_json([1, 2, 3])
        '[1, 2, 3]'
    """
    serializer = JSONSerializer()
    return serializer.serialize(obj)
