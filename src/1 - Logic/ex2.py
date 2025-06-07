def string_invertor(word: str) -> str:
    pos = len(word)
    string = [word[pos - i] for i in range(1, len(word) + 1)]
    return "".join(string)


string_inverter = lambda word: word[::-1]
