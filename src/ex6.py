from ex4 import cont_words

def fatoracao_number(num:int)->int:
    count = 0
    while count!=num:
        num*=(num-count)
        count+=1
    return num

def anagrama(word:str)->bool:
    words = cont_words(word)
    numerador = fatoracao_number(len(word))
    denominador = 0
    denominadores = []
    for i in words.values:
        denominadores.append(i)
    for i in denominadores:
        if i>1:
            denominador*=fatoracao_number(i)

    if denominador==0:
        return numerador
    else:
        return (numerador/denominador)
