from ex2 import string_invertor

def palindromo(word:str)->bool:
    return word==string_invertor(word)

def palindroms_using_points(word:str)->bool:
    left = 0
    right = len(word)-1

    while left<right:
        if word[left]!=word[right]:
            return False
        left+=1
        right-=1

    return True
