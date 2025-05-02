from ex2 import string_invertor

def romam_number_convertor(romam: str)->int:
    romam_number = {
        'I': 1,
        'V': 5,
        'X': 10,
        'L': 50,
        'C': 100,
        'D': 500,
        'M': 1000
    }

    total = 0
    prev_value = 0

    for i in string_invertor(romam):
        current_value = romam_number[i]

        if i not in romam_number:
            raise ValueError(f"'{i}' não é um número romano.")
        if current_value < prev_value:
            total -= current_value
        else:
            total += current_value

        prev_value = current_value