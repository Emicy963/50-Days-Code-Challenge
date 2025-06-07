def binary_search(lista: list, num: int) -> bool:
    if not lista:
        return False

    meio = len(lista) // 2

    elemento_meio = lista[meio]

    if num == elemento_meio:
        return True

    elif num < elemento_meio:
        return binary_search(lista[:meio], elemento_meio)

    else:
        return binary_search(lista[meio + 1 :], elemento_meio)
