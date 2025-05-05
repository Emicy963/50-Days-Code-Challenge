def bracket_valitor(word:str)->bool:
    if '(' in word and ')' in word:
        bracket = []
        for i in word:
            if i=='(':
                bracket.append(i)
            if i==')' and len(bracket)==0:
                return False
            elif i==')' and len(bracket)!=0:
                bracket.pop()
        return False if bracket else True
    else:
        return False
    