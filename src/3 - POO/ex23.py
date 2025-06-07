import heapq
import time


class Documento:
    """Classe que representa um documento a ser impresso."""

    def __init__(self, nome, prioridade=10, paginas=1):
        """
        Inicializa um novo documento.

        Args:
            nome (str): Nome do documento
            prioridade (int): Prioridade do documento (quanto menor, mais prioritário)
            paginas (int): Quantidade de páginas do documento
        """
        self.nome = nome
        self.prioridade = prioridade
        self.paginas = paginas
        self.timestamp = (
            time.time()
        )  # Para desempate entre documentos com mesma prioridade

    def __lt__(self, outro):
        """
        Compara documentos por prioridade e, em caso de empate, pelo timestamp.
        Necessário para o funcionamento correto do heapq.
        """
        if self.prioridade == outro.prioridade:
            return self.timestamp < outro.timestamp
        return self.prioridade < outro.prioridade

    def __str__(self):
        return f"Documento: {self.nome}, Prioridade: {self.prioridade}, Páginas: {self.paginas}"


class FilaDeImpressao:
    """Classe que gerencia uma fila de impressão com prioridade."""

    def __init__(self):
        """Inicializa uma fila de impressão vazia."""
        self.fila = []  # Heap que armazenará os documentos

    def adicionar_documento(self, documento):
        """
        Adiciona um documento à fila de impressão.

        Args:
            documento (Documento): O documento a ser adicionado
        """
        heapq.heappush(self.fila, documento)
        print(f"Adicionado à fila: {documento}")

    def imprimir_proximo(self):
        """
        Remove e 'imprime' o próximo documento com maior prioridade da fila.

        Returns:
            Documento ou None: O próximo documento a ser impresso ou None se a fila estiver vazia
        """
        if not self.fila:
            print("Fila vazia!")
            return None

        documento = heapq.heappop(self.fila)
        print(f"Imprimindo: {documento}")
        return documento

    def visualizar_fila(self):
        """
        Mostra todos os documentos na fila sem modificá-la.

        Returns:
            list: Lista de documentos ordenados por prioridade
        """
        # Cria uma cópia da fila para não alterá-la
        fila_temp = self.fila.copy()
        documentos = []

        print("Documentos na fila:")
        if not fila_temp:
            print("  Nenhum documento na fila")
            return []

        # Remove um por um para visualizar em ordem
        while fila_temp:
            doc = heapq.heappop(fila_temp)
            documentos.append(doc)
            print(f"  {doc}")

        return documentos

    def tamanho(self):
        """
        Retorna o número de documentos na fila.

        Returns:
            int: Número de documentos
        """
        return len(self.fila)
