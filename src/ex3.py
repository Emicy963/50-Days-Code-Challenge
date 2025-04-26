from ex2 import string_invertor

def palindromo(word:str)->bool:
    return True if word==string_invertor(word) else False