import random
import time
import threading
from queue import Queue


def simulador_fila_atendimento(num_clientes: int, num_atendentes: int) -> None:
    fila = Queue()

    for i in range(1, num_clientes + 1):
        fila.put(i)

    def atendente(id_atendente):
        while not fila.empty():
            try:
                cliente = fila.get_nowait()
            except:
                break
            print(f"Atendete, {id_atendente} está atendento o cliente: {cliente}")
            tempo = random.randint(1, 3)
            time.sleep(tempo)
            print(
                f"Atendente {id_atendente} terminou atendimento de {cliente} (tempo: {tempo}s)"
            )
            fila.task_done()

    threads = []
    for i in range(1, num_atendentes + 1):
        t = threading.Thread(target=atendente, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("\nTodos os clientes foram atendidos.")
