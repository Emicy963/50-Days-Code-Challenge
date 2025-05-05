def count_vowes_consonants(word: str)->dict:
    words = {
        "Consonants": 0,
        "Vowes": 0
    }
    for i in word.lower():
        if i.isalpha() and i in 'aeiou':
            words["Vowes"]+=1
        else:
            words["Consonants"]+=1
    return words
