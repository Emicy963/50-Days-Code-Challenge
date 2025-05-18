class ContaBancaria:
    # Método construtor (__init__) - Inicializa os atributos da conta bancária
    def __init__(self, amount: int, account_to_send_amount: int):
        self.amount = amount  # Saldo atual da conta
        self.account_to_send_amount = account_to_send_amount  # Saldo da conta de destino para transferências

    # Método para consultar o saldo disponível
    def consultar_dinheiro(self) -> str:
        """
        Método para verificar o saldo disponível na conta

        Returns:
            String com o valor disponível na conta
        """
        return f"Saldo disponível: {self.amount}"

    # Método para depositar dinheiro na conta
    def depositar_dinheiro(self, value: int) -> str:
        """
        Método que faz o deposito na conta

        Args:
            value: Valor a depositar

        Returns:
            String a dizer se o deposito foi feito com sucesso ou falhou
        """
        try:
            self.amount += value  # Adiciona o valor ao saldo atual
            return f"Deposito feito com sucesso!\n{self.consultar_dinheiro()}"  # Retorna mensagem de sucesso
        except Exception as err:
            return f"Erro ao depositar valor.\nErro:{str(err)}"  # Retorna mensagem de erro caso ocorra uma exceção

    # Método para levantar dinheiro da conta
    def levantar_dinheiro(self, value: int) -> str:
        """
        Método que faz o levantamento de dinheiro na conta.
        Este método verifica se o valor a levantar não é maior que o valor disponível na conta

        Args:
            value: Valor a levantar

        Returns:
            String a dizer se o levantamento foi feito com sucesso ou falhou
        """
        try:
            if value <= self.amount:  # Verifica se há saldo suficiente
                self.amount -= value  # Subtrai o valor do saldo atual
                return f"Dinheiro levantado com sucesso.\n{self.consultar_dinheiro}"  # Retorna mensagem de sucesso
            else:
                return f"Saldo insuficiente.\n\n{self.consultar_dinheiro}"  # Retorna mensagem de saldo insuficiente
        except Exception as err:
            return f"Erro ao levantar dinheiro. Erro: {str(err)}"  # Retorna mensagem de erro caso ocorra uma exceção

    # Método para transferir dinheiro para outra conta
    def transferir_dinheiro(self, value: int) -> str:
        """
        Método que faz o levantamento de dinheiro na conta.
        Este método verifica se o valor a transferir não é maior que o valor disponível na conta

        Args:
            value: Valor a transferir

        Returns:
            String a dizer se o levantamento foi feito com sucesso ou falhou
        """
        try:
            if value <= self.amount:  # Verifica se há saldo suficiente
                self.amount -= value  # Subtrai o valor do saldo atual
                self.account_to_send_amount += value  # Adiciona o valor ao saldo da conta de destino
                return f"Dinheiro transferido com sucesso.\n{self.consultar_dinheiro}"  # Retorna mensagem de sucesso
            else:
                return f"Saldo insuficiente.\n{self.consultar_dinheiro}"  # Retorna mensagem de saldo insuficiente
        except Exception as err:
            return f"Erro ao transferir dinheiro. Erro: {str(err)}"  # Retorna mensagem de erro caso ocorra uma exceção
