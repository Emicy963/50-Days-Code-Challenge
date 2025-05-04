from functools import reduce

def fatorial(num:int)->int:
    result=1
    while num:
        result *= num
        num -= 1
    return result

def anagrama(word:str)->bool:
    words = word.split()
    l = []
    def counter(w):
        d = {}
        for i in w:
            if i not in d:
                d[i] = 1
            else:
                d[i] += 1
        return d
    for j in words:
        l.append(counter(j))
    return reduce(lambda x, y: x==y, l)

def count_anagramas(word:str)->int:
    n = fatorial(len(word))
    h = {}
    for i in n:
        if i not in h:
            h[i] = 1
        else:
            h[i] += 1
    result = n//reduce(mul, [fatorial(j) for j in h.values()])
    return result
