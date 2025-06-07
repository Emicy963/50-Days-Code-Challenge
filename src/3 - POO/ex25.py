import unittest
from ex21 import ContaBancaria


class TesteContaBancaria(unittest.TestCase):
    def setUp(self):
        """
        Método executado antes de cada teste.
        Cria uma instância de ContaBancaria para ser usada nos testes.
        """
        self.conta = ContaBancaria(1000, 0)

    def test_consultar_dinheiro(self):
        """Testa o método consultar dinheiro"""
        self.assertEqual(self.conta.consultar_dinheiro(), "Saldo disponível: 1000")

    def test_depositar_dinheiro(self):
        """Testa o método depositar dinheiro"""
        result = self.conta.depositar_dinheiro(500)
        # Verificar se o resultado indica sucesso
        self.assertTrue("Deposito feito com sucesso" in result)
        # Verrificar se o saldo foi atualizado
        self.assertEqual(self.conta.amount, 1500)

    def test_levantar_dinheiro(self):
        """Testa o método levantar dinheiro"""
        result = self.conta.levantar_dinheiro(300)
        # Verificar se o resultado indica sucesso
        self.assertTrue("Dinheiro levantado com sucesso" in result)
        # Verificar se o saldo foi atualizado
        self.assertEqual(self.conta.amount, 700)

    def test_trasnsferir_dinheiro(self):
        """Testa o método transferir dinheiro"""
        result = self.conta.transferir_dinheiro(500)
        # Verificar se o resultado indica sucesso
        self.assertTrue("Dinheiro transferido com sucesso" in result)
        # Verificar se o conta principal foi subtraída
        self.assertEqual(self.conta.amount, 500)
        # Verficar se a conta recebeu o dinheiro
        self.assertEqual(self.conta.account_to_send_amount, 500)


if __name__ == "__main__":
    unittest.main()
