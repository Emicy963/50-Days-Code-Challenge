"""Resolution the problem using Bubble Sort"""
def bubble_sort(lista:list)->list:
    n = len(lista)

    for i in range(n):
        for j in range(0, n - 1 - 1):
            if lista[j] > lista[j + 1]:
                lista[j], lista[j + 1] = lista[j + 1], lista[j]

    return lista

"""Resolution the problem using Merge Sort"""
def merge_sort(lista:list)->list:
    if len(lista)<=1:
        return lista
    
    meio = len(lista) // 2
    esquerda = merge_sort(lista[:meio])
    direita = merge_sort(lista[meio:])

    return merge(esquerda, direita)

def merge(esq:list, dir:list)->list:
    result = []
    i = j = 0

    while i<len(esq) and j<len(dir):
        if esq[i] < dir[j]:
            result.append(esq[i])
            i+=1
        else:
            result.append(dir[j])
            j+=1
        
    result.extend(esq[i:])
    result.extend(dir[j:])
    return result
