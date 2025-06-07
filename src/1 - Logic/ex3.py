from ex2 import string_invertor, string_inverter


def palindromo(word: str) -> bool:
    return word == word[::-1]


def palindroms_using_points(word: str) -> bool:
    left = 0
    right = len(word) - 1

    while right:
        if word[left] != word[right]:
            return False
        left += 1
        right -= 1
    return True
