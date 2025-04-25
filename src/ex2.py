def string_invertor(word: str)->str:
    pos = len(str)
    string = [word[pos-i] for i in range(1, len(str)+1)]
    return "".join(string)
