class Produto:
    """
    Classe base para todos os produtos do sistema.
    Implementa os atributos e comportamentos comuns a todos os produtos.
    """

    def __init__(self, nome: str, preco: int, codigo: int, quantidade: int):
        self._nome = nome
        self._preco = preco
        self._codigo = codigo
        self._quantidade = quantidade

    # Getters e Setters para encapsulamento
    def get_nome(self) -> str:
        return self._nome

    def set_nome(self, nome: str):
        self._nome = nome

    def get_preco(self) -> int:
        return self._preco

    def set_preco(self, preco: int):
        if preco >= 0:
            self._preco = preco
        else:
            print("Erro: O preço não pode ser negativo.")

    def get_codigo(self) -> int:
        return self._codigo

    def get_quantidade(self) -> int:
        return self._quantidade

    def exibir_detalhes(self):
        """Exibe os detalhes do produto."""
        return f"""
        Produto: {self._nome}.
        Código: {self._codigo}.
        Preço: {self._preco:.2f}.
        Quantidade em estoque: {self._quantidade}.
        """

    def atualizar_estoque(self, quantidade: int):
        """Atualizar a quantidade de produtos em estoque"""
        novo_estoque = self._quantidade + quantidade
        if novo_estoque >= 0:
            self._quantidade = novo_estoque
            return True
        else:
            print("Erro: Quantidade em estoque insuficiente.")
            return False


class Livros(Produto):
    """
    Classe para representar livros, herda de Produto.
    Adiciona atributos específicos de livros.
    """

    def __init__(
        self,
        nome: str,
        preco: int,
        codigo: int,
        quantidade: int,
        autor: str,
        editora: str,
        numero_paginas: int,
    ):
        super().__init__(
            nome, preco, codigo, quantidade
        )  # Fazer o __init__ da classe pai
        self._autor = autor
        self._editora = editora
        self._numero_paginas = numero_paginas

    # Getters e Setters da classe filha
    def get_autor(self) -> str:
        return self._autor

    def get_editora(self) -> str:
        return self._editora

    def get_numero_paginas(self) -> int:
        return self._numero_paginas

    def set_autor(self, autor: str):
        self._autor = autor

    def set_editora(self, editora: str):
        self._editora = editora

    def set_numero_paginas(self, numero_paginas: int):
        if numero_paginas >= 0:
            self._numero_paginas = numero_paginas
        else:
            print("Erro: O número de páginas tem que ser positivo.")

    # Polimorfismo: subscrever um método da classe pai
    def exibir_detalhes(self):
        """Subscrever o método para exibir detalhes específicos dos livros"""
        detalhes_base = super().exibir_detalhes()
        detalhes_livro = f"""
        ----- Detalhes do Livros -----
        Autor: {self._autor}.
        Editora: {self._editora}.
        Número de páginas: {self._numero_paginas}.
        """
        return detalhes_base + detalhes_livro


class Eletronicos(Produto):
    """
    Classe para representar eletrônicos, herda de Produto.
    Adiciona atributos específicos de eletrônicos.
    """

    def __init__(
        self,
        nome: str,
        preco: int,
        codigo: int,
        quantidade: int,
        marca: str,
        modelo: str,
        garantia: int,
    ):
        super().__init__(
            nome, preco, codigo, quantidade
        )  # Fazendo o __init__ da classe Pai
        # Adicionar atributos específcos da classe filho
        self._marca = marca
        self._modelo = modelo
        self._garantia = garantia  # Em meses

    # Getters e Setters específicos dessa classe
    def get_marca(self) -> str:
        return self._marca

    def get_modelo(self) -> str:
        return self._modelo

    def get_garantia(self) -> int:
        return self._garantia

    def set_marca(self, marca: str):
        self._marca = marca

    def set_modelo(self, modelo: str):
        self._modelo = modelo

    def set_garantia(self, garantia: int):
        if garantia >= 0:
            self._garantia = garantia
        else:
            print("Erro: A garantia não posso ser negativa.")

    # Polimorfismo: sobrescrever métodos da classe Pai
    def exibir_detalhes(self):
        """Sobrescrever o método para incluir detalhes específicos dos eletrônicos"""
        detalhes_base = super().exibir_detalhes()
        detalhes_eletronico = f"""
        ----- Detalhes dos Eletrônico -----
        Marca: {self._marca}.
        Modelo: {self._modelo}.
        Garantia: {self._garantia} meses.
        """
        return detalhes_base + detalhes_eletronico
