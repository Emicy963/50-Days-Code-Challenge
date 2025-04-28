def bracket_valitor(word:str)->bool:
    if '(' and ')' in word:
        for i in range(len(word)//2):
            if word[i] == ')':
                return False
            elif word[i] == '(':
                pos = len(word)
                for i, j in enumerate(word, start=1):
                    if word[pos-i]==')'
    